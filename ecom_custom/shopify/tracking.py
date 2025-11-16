from __future__ import annotations

import json
import frappe
from frappe.utils import now_datetime
from shopify.resources import Fulfillment

from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import FULLFILLMENT_ID_FIELD


def populate_delivery_note_tracking(doc, method=None):  # noqa: ANN001
	"""Hook for Delivery Note events to fetch Shopify tracking numbers."""

	fulfillment_id = doc.get(FULLFILLMENT_ID_FIELD)
	if not fulfillment_id:
		return

	tracking_payload = _get_tracking_payload(fulfillment_id)
	if not tracking_payload:
		return

	_tracking_numbers = tracking_payload.get("tracking_numbers") or []
	if _tracking_numbers:
		doc.tracking_no = ", ".join(_tracking_numbers)

	if tracking_payload.get("tracking_company"):
		doc.transporter_name = tracking_payload.get("tracking_company")

	if tracking_payload.get("tracking_urls"):
		doc.shopify_tracking_urls = "\n".join(tracking_payload["tracking_urls"])

	_store_tracking_snapshot(doc, tracking_payload)


@temp_shopify_session
def _get_tracking_payload(fulfillment_id: str | int) -> dict | None:
	try:
		fulfillment = Fulfillment.find(fulfillment_id)
	except Exception:  # pragma: no cover - depends on Shopify responses
		frappe.log_error(
			title="Shopify tracking fetch failed",
			message=f"Unable to load fulfillment {fulfillment_id}",
		)
		return None

	data = fulfillment.to_dict()
	numbers: list[str] = []
	urls: list[str] = []

	if data.get("tracking_numbers"):
		numbers.extend([value for value in data["tracking_numbers"] if value])
	elif data.get("tracking_number"):
		numbers.append(data.get("tracking_number"))

	if data.get("tracking_urls"):
		urls.extend([value for value in data["tracking_urls"] if value])
	elif data.get("tracking_url"):
		urls.append(data.get("tracking_url"))

	return {
		"tracking_numbers": numbers,
		"tracking_urls": urls,
		"tracking_company": data.get("tracking_company"),
	}


def _store_tracking_snapshot(doc, payload: dict) -> None:  # noqa: ANN001
	tracking_numbers = payload.get("tracking_numbers") or []
	tracking_urls = payload.get("tracking_urls") or []

	entry = {
		"delivery_note": doc.name,
		"tracking_numbers": tracking_numbers,
		"tracking_urls": tracking_urls,
		"tracking_company": payload.get("tracking_company"),
		"synced_on": now_datetime().isoformat(),
	}

	linked_sales_orders = _get_linked_sales_orders(doc)
	for so_name in linked_sales_orders:
		existing_raw = frappe.db.get_value("Sales Order", so_name, "shopify_tracking_info") or "[]"
		try:
			existing_entries = json.loads(existing_raw)
		except json.JSONDecodeError:
			existing_entries = []

		# replace previous entry for the same Delivery Note
		existing_entries = [row for row in existing_entries if row.get("delivery_note") != doc.name]
		existing_entries.append(entry)

		frappe.db.set_value(
			"Sales Order",
			so_name,
			"shopify_tracking_info",
			json.dumps(existing_entries, sort_keys=True),
			update_modified=False,
		)


def _get_linked_sales_orders(doc) -> set[str]:  # noqa: ANN001
	orders = {item.against_sales_order for item in doc.items if getattr(item, "against_sales_order", None)}
	if doc.get("against_sales_order"):
		orders.add(doc.get("against_sales_order"))
	return {order for order in orders if order}
