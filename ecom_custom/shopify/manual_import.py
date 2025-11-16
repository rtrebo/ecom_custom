from __future__ import annotations

import frappe
from shopify.resources import Order

from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecom_custom.shopify import order_overrides


def import_order(order_id: int | str) -> str | None:
	"""Fetch a single Shopify order and run it through our sync pipeline."""

	payload = _fetch_order_payload(order_id)
	if not payload:
		frappe.throw(f"Order {order_id} not found in Shopify")

	order_overrides.sync_sales_order(payload)
	return frappe.db.get_value("Sales Order", {"shopify_order_id": str(order_id)})


@temp_shopify_session
def _fetch_order_payload(order_id: int | str) -> dict | None:
	order = Order.find(order_id)
	return order.to_dict() if order else None
