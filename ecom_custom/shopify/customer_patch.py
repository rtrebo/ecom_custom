import frappe

# Placeholder used when Shopify does not provide a fiscal code.
DEFAULT_FISCAL_CODE = "0000000000000000"


def _ensure_fiscal_code(self):
	if not frappe.db.has_column("Customer", "fiscal_code"):
		return

	try:
		customer_doc = self.get_customer_doc()
	except frappe.DoesNotExistError:
		return

	if customer_doc.fiscal_code:
		return

	customer_doc.fiscal_code = DEFAULT_FISCAL_CODE
	customer_doc.flags.ignore_mandatory = True
	customer_doc.save(ignore_permissions=True)


def _wrap_and_ensure(method):
	def wrapped(self, *args, **kwargs):
		result = method(self, *args, **kwargs)
		_ensure_fiscal_code(self)
		return result

	return wrapped


def apply():
	from ecommerce_integrations.shopify.customer import ShopifyCustomer

	# Patch methods to set a default fiscal code on customer creation/updates.
	ShopifyCustomer._ensure_fiscal_code = _ensure_fiscal_code
	ShopifyCustomer.sync_customer = _wrap_and_ensure(ShopifyCustomer.sync_customer)
	ShopifyCustomer.update_existing_addresses = _wrap_and_ensure(
		ShopifyCustomer.update_existing_addresses
	)
