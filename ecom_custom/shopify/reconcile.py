from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import get_datetime
from shopify.resources import Order

from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import ORDER_ID_FIELD
from ecom_custom.shopify import order_overrides


def reconcile_sales_orders(order_names: Sequence[str] | None = None, limit: int | None = None) -> dict[str, Any]:
	"""Re-fetch Shopify payloads for existing Sales Orders and update their metadata."""

	if order_names:
		targets = [
			{"name": name, ORDER_ID_FIELD: frappe.db.get_value("Sales Order", name, ORDER_ID_FIELD)}
			for name in order_names
		]
	else:
		targets = frappe.get_all(
			"Sales Order",
			filters={ORDER_ID_FIELD: ["is", "set"]},
			fields=["name", ORDER_ID_FIELD, "transaction_date"],
			limit=limit or 0,
		)

	stats = {"total": len(targets), "updated": 0, "missing": [], "errors": {}}
	payload_cache = _bulk_fetch_payloads(targets) if not order_names else {}

	for row in targets:
		order_id = row.get(ORDER_ID_FIELD)
		if not order_id:
			stats["missing"].append(row["name"])
			continue

		payload = payload_cache.get(str(order_id))
		if not payload:
			payload = _fetch_order_payload(order_id)

		if not payload:
			stats["missing"].append(row["name"])
			continue

		try:
			order_overrides._post_process_sales_order(payload, row["name"])  # type: ignore[attr-defined]
		except Exception as exc:  # pragma: no cover - defensive safeguard
			stats["errors"][row["name"]] = str(exc)
			continue

		stats["updated"] += 1

	return stats


def _bulk_fetch_payloads(targets: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
	if not targets:
		return {}

	dates = [row.get("transaction_date") for row in targets if row.get("transaction_date")]
	if not dates:
		return {}

	start = get_datetime(min(dates)) - timedelta(days=1)
	end = get_datetime(max(dates)) + timedelta(days=1)

	cache: dict[str, dict[str, Any]] = {}
	for order in order_overrides.fetch_old_orders_any(start, end):
		cache[str(order.get("id"))] = order

	return cache


@temp_shopify_session
def _fetch_order_payload(order_id: str | int) -> dict[str, Any] | None:
	try:
		order = Order.find(order_id)
	except Exception:
		return None

	return order.to_dict() if order else None
