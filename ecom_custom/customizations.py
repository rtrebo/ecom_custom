from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def ensure_custom_fields() -> None:
	"""Create custom fields required by the Shopify overrides.

	This can safely be re-run; frappe will ignore fields that already exist.
	"""

	shipping_fields = [
		("shopify_shipping_name", "Data", "Shopify Shipping Name"),
		("shopify_shipping_first_name", "Data", "Shopify Shipping First Name"),
		("shopify_shipping_last_name", "Data", "Shopify Shipping Last Name"),
		("shopify_shipping_company", "Data", "Shopify Shipping Company"),
		("shopify_shipping_address1", "Data", "Shopify Shipping Address Line 1"),
		("shopify_shipping_address2", "Data", "Shopify Shipping Address Line 2"),
		("shopify_shipping_city", "Data", "Shopify Shipping City"),
		("shopify_shipping_province", "Data", "Shopify Shipping Province"),
		("shopify_shipping_province_code", "Data", "Shopify Shipping Province Code"),
		("shopify_shipping_postal_code", "Data", "Shopify Shipping Postal Code"),
		("shopify_shipping_country", "Data", "Shopify Shipping Country"),
		("shopify_shipping_country_code", "Data", "Shopify Shipping Country Code"),
	]

	billing_fields = [
		("shopify_billing_name", "Data", "Shopify Billing Name"),
		("shopify_billing_first_name", "Data", "Shopify Billing First Name"),
		("shopify_billing_last_name", "Data", "Shopify Billing Last Name"),
		("shopify_billing_company", "Data", "Shopify Billing Company"),
		("shopify_billing_address1", "Data", "Shopify Billing Address Line 1"),
		("shopify_billing_address2", "Data", "Shopify Billing Address Line 2"),
		("shopify_billing_city", "Data", "Shopify Billing City"),
		("shopify_billing_province", "Data", "Shopify Billing Province"),
		("shopify_billing_province_code", "Data", "Shopify Billing Province Code"),
		("shopify_billing_postal_code", "Data", "Shopify Billing Postal Code"),
		("shopify_billing_country", "Data", "Shopify Billing Country"),
		("shopify_billing_country_code", "Data", "Shopify Billing Country Code"),
	]

	def _make_address_fields(prefix_fields, insert_after):
		fields = []
		for fieldname, fieldtype, label in prefix_fields:
			fields.append(
				{
					"fieldname": fieldname,
					"label": label,
					"fieldtype": fieldtype,
					"insert_after": insert_after,
					"read_only": 1,
					"allow_on_submit": 1,
				}
			)
			insert_after = fieldname
		return fields

	custom_fields = {
		"Sales Order": (
			[
				{
					"fieldname": "shopify_shipping_address_json",
					"label": "Shopify Shipping Address JSON",
					"fieldtype": "Small Text",
					"insert_after": "shipping_address_name",
					"read_only": 1,
					"allow_on_submit": 1,
				},
			]
			+ _make_address_fields(shipping_fields, "shopify_shipping_address_json")
			+ [
				{
					"fieldname": "shopify_shipping_email",
					"label": "Shopify Shipping Email",
					"fieldtype": "Data",
					"insert_after": shipping_fields[-1][0],
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "shopify_shipping_phone",
					"label": "Shopify Shipping Phone",
					"fieldtype": "Data",
					"insert_after": "shopify_shipping_email",
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "shopify_billing_address_json",
					"label": "Shopify Billing Address JSON",
					"fieldtype": "Small Text",
					"insert_after": "customer_address",
					"read_only": 1,
					"allow_on_submit": 1,
				},
			]
			+ _make_address_fields(billing_fields, "shopify_billing_address_json")
			+ [
				{
					"fieldname": "shopify_billing_email",
					"label": "Shopify Billing Email",
					"fieldtype": "Data",
					"insert_after": billing_fields[-1][0],
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "shopify_billing_phone",
					"label": "Shopify Billing Phone",
					"fieldtype": "Data",
					"insert_after": "shopify_billing_email",
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "shopify_info_section",
					"label": "Shopify Order Info",
					"fieldtype": "Section Break",
					"insert_after": "discount_amount",
				},
				{
					"fieldname": "shopify_payment_gateways",
					"label": "Shopify Payment Gateways",
					"fieldtype": "Small Text",
					"insert_after": "shopify_info_section",
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "shopify_cash_on_delivery",
					"label": "Cash on Delivery",
					"fieldtype": "Check",
					"insert_after": "shopify_payment_gateways",
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "shopify_discount_codes",
					"label": "Shopify Discount Codes",
					"fieldtype": "Data",
					"insert_after": "shopify_cash_on_delivery",
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "shopify_discount_amount",
					"label": "Shopify Discount Amount",
					"fieldtype": "Currency",
					"insert_after": "shopify_discount_codes",
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "shopify_tracking_info",
					"label": "Shopify Tracking Entries",
					"fieldtype": "Small Text",
					"insert_after": "shopify_discount_amount",
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "shopify_last_synced_at",
					"label": "Shopify Last Synced At",
					"fieldtype": "Datetime",
					"insert_after": "shopify_tracking_info",
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "shopify_cancel_reason",
					"label": "Shopify Cancel Reason",
					"fieldtype": "Data",
					"insert_after": "shopify_last_synced_at",
					"read_only": 1,
					"allow_on_submit": 1,
				},
			]
		),
		"Delivery Note": [
			{
				"fieldname": "shopify_tracking_urls",
				"label": "Shopify Tracking URLs",
				"fieldtype": "Small Text",
				"insert_after": "tracking_no",
				"read_only": 1,
				"allow_on_submit": 1,
			},
		],
	}

	create_custom_fields(custom_fields, ignore_validate=True)
	_update_field_layouts()


def _update_field_layouts() -> None:
	layout_map = {
		"Sales Order": {
			"shopify_payment_gateways": "shopify_info_section",
			"shopify_cash_on_delivery": "shopify_payment_gateways",
			"shopify_discount_codes": "shopify_cash_on_delivery",
			"shopify_discount_amount": "shopify_discount_codes",
			"shopify_tracking_info": "shopify_discount_amount",
			"shopify_last_synced_at": "shopify_tracking_info",
			"shopify_cancel_reason": "shopify_last_synced_at",
		}
	}

	for doctype, mapping in layout_map.items():
		for fieldname, insert_after in mapping.items():
			custom_field = f"{doctype}-{fieldname}"
			if frappe.db.exists("Custom Field", custom_field):
				frappe.db.set_value("Custom Field", custom_field, "insert_after", insert_after)
