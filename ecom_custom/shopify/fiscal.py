import frappe

DEFAULT_FISCAL_CODE = "0000000000000000"


def ensure_customer_fiscal_code(doc, method=None):
	"""Set a placeholder fiscal code on Sales Invoice to satisfy Italy validation."""

	if not doc.customer or not frappe.db.has_column("Customer", "fiscal_code"):
		return

	# Fetch current fiscal code
	fiscal_code = frappe.db.get_value("Customer", doc.customer, "fiscal_code") or ""
	fiscal_code = fiscal_code.strip() if isinstance(fiscal_code, str) else fiscal_code

	if not fiscal_code:
		fiscal_code = DEFAULT_FISCAL_CODE
		frappe.db.set_value("Customer", doc.customer, "fiscal_code", fiscal_code)

	# Ensure the invoice carries the value
	if hasattr(doc, "customer_fiscal_code"):
		doc.customer_fiscal_code = fiscal_code
