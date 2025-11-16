from __future__ import annotations

import frappe

from ecommerce_integrations.shopify import order as shopify_order
from ecom_custom.shopify import order_overrides


def enqueue_old_orders_sync(start: str | None = None, end: str | None = None):
	shopify_order.sync_sales_order = order_overrides.sync_sales_order
	shopify_order._fetch_old_orders = order_overrides.fetch_old_orders_any

	if start:
		frappe.db.set_value("Shopify Setting", "Shopify Setting", "old_orders_from", start)
	if end:
		frappe.db.set_value("Shopify Setting", "Shopify Setting", "old_orders_to", end)

	frappe.db.set_value("Shopify Setting", "Shopify Setting", "sync_old_orders", 1)
	frappe.db.commit()

	frappe.enqueue(
		shopify_order.sync_old_orders,
		queue="long",
		job_name="Shopify Old Orders Sync",
	)
	return "enqueued"
