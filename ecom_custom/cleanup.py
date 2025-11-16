from __future__ import annotations

import frappe


def delete_shopify_orders() -> dict[str, int]:
	"""Delete every Sales Order that originated from Shopify (including linked docs).

	This is destructive. It cancels and deletes linked Delivery Notes and Sales Invoices
	before removing the Sales Order itself.
	"""

	stats = {"Sales Order": 0, "Delivery Note": 0, "Sales Invoice": 0}

	sales_orders = frappe.get_all("Sales Order", filters={"shopify_order_id": ["is", "set"]}, pluck="name")

	for so_name in sales_orders:
		for dn_name in _linked_delivery_notes(so_name):
			_cancel_and_delete("Delivery Note", dn_name)
			stats["Delivery Note"] += 1

		for si_name in _linked_sales_invoices(so_name):
			_cancel_and_delete("Sales Invoice", si_name)
			stats["Sales Invoice"] += 1

		_cancel_and_delete("Sales Order", so_name, ignore_links=True)
		stats["Sales Order"] += 1

	return stats


def _linked_delivery_notes(sales_order: str) -> set[str]:
	dn_items = frappe.get_all(
		"Delivery Note Item",
		filters={"against_sales_order": sales_order},
		pluck="parent",
		distinct=True,
	)
	return {name for name in dn_items if name}


def _linked_sales_invoices(sales_order: str) -> set[str]:
	si_items = frappe.get_all(
		"Sales Invoice Item",
		filters={"sales_order": sales_order},
		pluck="parent",
		distinct=True,
	)
	return {name for name in si_items if name}


def _cancel_and_delete(doctype: str, name: str, ignore_links: bool = False) -> None:
	doc = frappe.get_doc(doctype, name)
	if ignore_links:
		doc.flags.ignore_links = True

	if doc.docstatus == 1:
		doc.cancel()

	frappe.delete_doc(
		doctype,
		name,
		ignore_permissions=True,
		force=True,
		ignore_missing=True,
	)
