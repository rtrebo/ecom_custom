__version__ = "0.0.1"


def _patch_shopify_handlers() -> None:
	try:
		from ecommerce_integrations.shopify import order as base_order
		from ecom_custom.shopify import order_overrides

		base_order.sync_sales_order = order_overrides.sync_sales_order
	except Exception:
		# During certain bench commands the dependency might not be available yet.
		pass


_patch_shopify_handlers()
