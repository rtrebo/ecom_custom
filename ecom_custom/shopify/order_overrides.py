from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, cstr, flt, now_datetime
from ecommerce_integrations.shopify.connection import temp_shopify_session
from frappe.utils.nestedset import get_root_of

from ecommerce_integrations.shopify import order as shopify_order_module
from ecommerce_integrations.shopify.constants import ORDER_ID_FIELD, ORDER_NUMBER_FIELD, ORDER_STATUS_FIELD, SETTING_DOCTYPE
from ecommerce_integrations.shopify.customer import ShopifyCustomer
from ecommerce_integrations.shopify.utils import create_shopify_log

_BASE_SYNC_SALES_ORDER = shopify_order_module.sync_sales_order


def sync_sales_order(payload: dict[str, Any], request_id: str | None = None) -> None:
	"""Extend the default behaviour so we can re-sync existing orders.

	New orders go through the upstream implementation first. When the order already exists,
	we update metadata rather than returning early.
	"""

	order = payload or {}
	order_id = cstr(order.get("id"))

	frappe.set_user("Administrator")
	frappe.flags.request_id = request_id

	sales_order = frappe.db.get_value("Sales Order", {ORDER_ID_FIELD: order_id})
	if not sales_order:
		_BASE_SYNC_SALES_ORDER(payload, request_id)
		sales_order = frappe.db.get_value("Sales Order", {ORDER_ID_FIELD: order_id})
		if sales_order:
			_post_process_sales_order(order, sales_order)
		return

	try:
		_post_process_sales_order(order, sales_order)
	except Exception as exc:  # pragma: no cover
		create_shopify_log(status="Error", exception=exc, rollback=True)
	else:
		create_shopify_log(status="Success", message=f"Sales Order {sales_order} updated from Shopify payload")


def _post_process_sales_order(order: dict[str, Any], sales_order: str) -> None:
	_ensure_customer_addresses(order)
	_apply_updates(sales_order, order)


@temp_shopify_session
def fetch_old_orders_any(from_time, to_time):
	from frappe.utils import get_datetime
	from shopify.collection import PaginatedIterator
	from shopify.resources import Order

	from_time = get_datetime(from_time).astimezone().isoformat()
	to_time = get_datetime(to_time).astimezone().isoformat()

	orders_iterator = PaginatedIterator(
		Order.find(created_at_min=from_time, created_at_max=to_time, limit=250, status="any")
	)

	results = []
	for orders in orders_iterator:
		for order in orders:
			results.append(order.to_dict())

	return results


shopify_order_module.sync_sales_order = sync_sales_order
shopify_order_module._fetch_old_orders = fetch_old_orders_any


def _ensure_customer_addresses(order: dict[str, Any]) -> None:
	shopify_customer = order.get("customer") or {}
	if not isinstance(shopify_customer, dict):
		return

	customer_id = shopify_customer.get("id")
	if not customer_id:
		return

	shopify_customer["billing_address"] = (
		order.get("billing_address") or shopify_customer.get("billing_address") or {}
	)
	shopify_customer["shipping_address"] = (
		order.get("shipping_address") or shopify_customer.get("shipping_address") or {}
	)

	customer = ShopifyCustomer(customer_id=customer_id)
	if not customer.is_synced():
		customer.sync_customer(customer=shopify_customer)
	else:
		customer.update_existing_addresses(shopify_customer)

	_apply_customer_metadata(customer, shopify_customer, order)
	_refresh_address_docs(customer, shopify_customer, order)
	_update_customer_territory(customer, order)


def _apply_updates(sales_order: str, order: dict[str, Any]) -> None:
	updates: dict[str, Any] = {"shopify_last_synced_at": now_datetime()}

	if order.get("name"):
		updates[ORDER_NUMBER_FIELD] = order["name"]

	if order.get("financial_status"):
		updates[ORDER_STATUS_FIELD] = order["financial_status"]

	if "cancel_reason" in order:
		updates["shopify_cancel_reason"] = order.get("cancel_reason")

	shipping_snapshot = _address_snapshot(order.get("shipping_address"), prefix="shipping", default_email=order.get("email"))
	billing_snapshot = _address_snapshot(order.get("billing_address"), prefix="billing", default_email=order.get("email"))

	if shipping_snapshot:
		updates.update(shipping_snapshot)

	if billing_snapshot:
		updates.update(billing_snapshot)

	discount_snapshot = _discount_snapshot(order)
	if discount_snapshot:
		updates.update(discount_snapshot)

	payment_snapshot = _payment_snapshot(order)
	if payment_snapshot:
		updates.update(payment_snapshot)

	if updates:
		_set_existing_fields("Sales Order", sales_order, updates)

	_mark_order_fulfillment_status(sales_order, order)


def _address_snapshot(address: dict[str, Any] | None, *, prefix: str, default_email: str | None) -> dict[str, Any]:
	if not isinstance(address, dict):
		return {}

	base_fields = {
		f"shopify_{prefix}_address_json": json.dumps(address, sort_keys=True),
		f"shopify_{prefix}_name": address.get("name"),
		f"shopify_{prefix}_first_name": address.get("first_name"),
		f"shopify_{prefix}_last_name": address.get("last_name"),
		f"shopify_{prefix}_company": address.get("company"),
		f"shopify_{prefix}_address1": address.get("address1"),
		f"shopify_{prefix}_address2": address.get("address2"),
		f"shopify_{prefix}_city": address.get("city"),
		f"shopify_{prefix}_province": address.get("province"),
		f"shopify_{prefix}_province_code": address.get("province_code"),
		f"shopify_{prefix}_postal_code": address.get("zip"),
		f"shopify_{prefix}_country": address.get("country"),
		f"shopify_{prefix}_country_code": address.get("country_code"),
		f"shopify_{prefix}_email": address.get("email") or default_email,
		f"shopify_{prefix}_phone": address.get("phone"),
	}

	return {field: value for field, value in base_fields.items() if value not in (None, "")}


def _discount_snapshot(order: dict[str, Any]) -> dict[str, Any]:
	raw_codes = order.get("discount_codes") or []
	if not isinstance(raw_codes, list):
		return {}

	codes: list[str] = []
	amount = 0.0
	for row in raw_codes:
		if not isinstance(row, dict):
			continue
		if row.get("code"):
			codes.append(row["code"])
		amount += flt(row.get("amount"))

	return {
		"shopify_discount_codes": ", ".join(codes) if codes else None,
		"shopify_discount_amount": amount,
	}


def _payment_snapshot(order: dict[str, Any]) -> dict[str, Any]:
	raw_gateways = order.get("payment_gateway_names") or []
	gateways = [
		cstr(value).strip()
		for value in raw_gateways
		if isinstance(value, (str, bytes)) and cstr(value).strip()
	]

	is_cod = _is_cash_on_delivery(gateways, order)

	return {
		"shopify_payment_gateways": ", ".join(gateways) if gateways else None,
		"shopify_cash_on_delivery": 1 if is_cod else 0,
	}


def _mark_order_fulfillment_status(sales_order: str, order: dict[str, Any]) -> None:
	doc = frappe.db.get_value(
		"Sales Order",
		sales_order,
		["per_delivered", "status", "docstatus"],
		as_dict=True,
	)

	if not doc or doc.docstatus != 1:
		return

	is_fulfilled = _is_fulfilled(order)
	values = {}
	if is_fulfilled:
		if doc.per_delivered is None or doc.per_delivered < 100:
			values["per_delivered"] = 100

		if doc.status != "Completed":
			values["status"] = "Completed"
	else:
		if _has_delivery_activity(sales_order):
			return

		if doc.per_delivered and doc.per_delivered > 0:
			values["per_delivered"] = 0

		if doc.status == "Completed":
			values["status"] = "To Deliver and Bill"

	if values:
		_set_existing_fields("Sales Order", sales_order, values, update_modified=False)


def _is_fulfilled(order: dict[str, Any]) -> bool:
	if order.get("fulfillment_status") == "fulfilled":
		return True
	if order.get("closed_at"):
		return True
	return False


def _has_delivery_activity(sales_order: str) -> bool:
	return bool(
		frappe.db.exists(
			"Delivery Note Item",
			{"against_sales_order": sales_order, "docstatus": 1},
		)
	)


def _is_cash_on_delivery(gateways: list[str], order: dict[str, Any]) -> bool:
	cod_keywords = ("cash on delivery", "cod", "contrassegno")

	for gateway in gateways:
		lower_gateway = gateway.lower()
		if any(keyword in lower_gateway for keyword in cod_keywords):
			return True

	for shipping_line in order.get("shipping_lines") or []:
		for key in ("title", "code"):
			value = cstr(shipping_line.get(key)).strip().lower()
			if value and any(keyword in value for keyword in cod_keywords):
				return True

	payment_terms = order.get("payment_terms") or {}
	for key in ("payment_terms_name", "payment_terms_type"):
		value = cstr(payment_terms.get(key)).strip().lower()
		if value and any(keyword in value for keyword in cod_keywords):
			return True

	return False


def _apply_customer_metadata(customer: ShopifyCustomer, shopify_customer: dict[str, Any], order: dict[str, Any]) -> None:
	try:
		customer_doc = customer.get_customer_doc()
	except frappe.DoesNotExistError:
		return

	updates: dict[str, Any] = {}
	first_name = (shopify_customer.get("first_name") or "").strip()
	last_name = (shopify_customer.get("last_name") or "").strip()

	if customer_doc.meta.has_field("first_name") and first_name and customer_doc.first_name != first_name:
		updates["first_name"] = first_name

	if customer_doc.meta.has_field("last_name") and last_name and customer_doc.last_name != last_name:
		updates["last_name"] = last_name

	email = (shopify_customer.get("email") or order.get("email") or "").strip()
	if email and customer_doc.meta.has_field("email_id") and customer_doc.email_id != email:
		updates["email_id"] = email

	if updates:
		customer_doc.update(updates)
		customer_doc.flags.ignore_mandatory = True
		customer_doc.save(ignore_permissions=True)


def _set_existing_fields(doctype: str, name: str, values: dict[str, Any], update_modified: bool = False) -> None:
	"""Set only those fields that actually exist on the DocType."""

	if not values:
		return

	meta = frappe.get_meta(doctype)
	valid_values = {field: val for field, val in values.items() if meta.has_field(field)}

	if not valid_values:
		return

	frappe.db.set_value(doctype, name, valid_values, update_modified=update_modified)


def _refresh_address_docs(customer: ShopifyCustomer, shopify_customer: dict[str, Any], order: dict[str, Any]) -> None:
	mapping = {
		"Shipping": shopify_customer.get("shipping_address") or order.get("shipping_address"),
		"Billing": shopify_customer.get("billing_address") or order.get("billing_address"),
	}

	for address_type, address_data in mapping.items():
		if not isinstance(address_data, dict):
			continue

		address_doc = customer.get_customer_address_doc(address_type)
		if not address_doc:
			continue

		update_dict = _sanitize_address_fields(address_data)
		update_dict["email_id"] = address_data.get("email") or shopify_customer.get("email") or order.get("email")
		update_dict["phone"] = address_data.get("phone")
		update_dict["address_title"] = (
			address_data.get("name") or customer.get_customer_doc().customer_name or address_doc.address_title
		)

		address_doc.update({k: v for k, v in update_dict.items() if v not in (None, "")})
		address_doc.flags.ignore_version = True
		address_doc.flags.ignore_mandatory = True
		address_doc.save(ignore_permissions=True)


def _sanitize_address_fields(address: dict[str, Any]) -> dict[str, Any]:
	def clean(value: str | None) -> str | None:
		if not value:
			return value
		value = value.strip()
		return value if "@" not in value else ""

	return {
		"address_line1": clean(address.get("address1")) or clean(address.get("name")),
		"address_line2": clean(address.get("address2")),
		"city": clean(address.get("city")),
		"state": clean(address.get("province")),
		"pincode": clean(address.get("zip")),
		"country": clean(address.get("country")),
	}


def _update_customer_territory(customer: ShopifyCustomer, order: dict[str, Any]) -> None:
	try:
		customer_doc = customer.get_customer_doc()
	except frappe.DoesNotExistError:
		return

	shipping_address = order.get("shipping_address") or {}
	territory_name = shipping_address.get("country")
	if not territory_name:
		return

	territory = _ensure_territory_exists(territory_name)
	if territory and customer_doc.territory != territory:
		customer_doc.territory = territory
		customer_doc.flags.ignore_mandatory = True
		customer_doc.save(ignore_permissions=True)


def _ensure_territory_exists(name: str | None) -> str | None:
	if not name:
		return None

	if frappe.db.exists("Territory", name):
		return name

	root = get_root_of("Territory")
	try:
		frappe.get_doc(
			{
				"doctype": "Territory",
				"territory_name": name,
				"parent_territory": root,
			}
		).insert(ignore_permissions=True)
	except Exception:  # pragma: no cover
		frappe.log_error(message=frappe.get_traceback(), title=f"Unable to create Territory {name}")
		return None

	return name
