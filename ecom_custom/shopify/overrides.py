import frappe

from ecommerce_integrations.ecommerce_integrations.doctype.ecommerce_integration_log.ecommerce_integration_log import (
	create_log,
)
from ecommerce_integrations.shopify.constants import MODULE_NAME, SETTING_DOCTYPE


def skip_migrate_from_old_connector(payload=None, request_id=None):
	"""Short-circuit the legacy migration step for Shopify.

	This instance never used the old connector, so we immediately mark the migration as done.
	"""

	if request_id:
		log = frappe.get_doc("Ecommerce Integration Log", request_id)
	else:
		log = create_log(
			module_def=MODULE_NAME,
			status="Queued",
			method="ecom_custom.shopify.overrides.skip_migrate_from_old_connector",
		)

	frappe.db.set_value(SETTING_DOCTYPE, SETTING_DOCTYPE, "is_old_data_migrated", 1)

	log.status = "Success"
	log.response_data = {"message": "Skipped migration via ecom_custom"}
	log.save(ignore_permissions=True)

	return True
