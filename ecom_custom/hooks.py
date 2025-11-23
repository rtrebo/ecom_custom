app_name = "ecom_custom"
app_title = "Ecom Custom"
app_publisher = "Roland Trebo"
app_description = "Custom ecommerce logic"
app_email = "roland@example.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "ecom_custom",
# 		"logo": "/assets/ecom_custom/logo.png",
# 		"title": "Ecom Custom",
# 		"route": "/ecom_custom",
# 		"has_permission": "ecom_custom.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ecom_custom/css/ecom_custom.css"
# app_include_js = "/assets/ecom_custom/js/ecom_custom.js"

# include js, css files in header of web template
# web_include_css = "/assets/ecom_custom/css/ecom_custom.css"
# web_include_js = "/assets/ecom_custom/js/ecom_custom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ecom_custom/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "ecom_custom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "ecom_custom.utils.jinja_methods",
# 	"filters": "ecom_custom.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "ecom_custom.customizations.ensure_custom_fields"
after_migrate = "ecom_custom.customizations.ensure_custom_fields"

# Uninstallation
# ------------

# before_uninstall = "ecom_custom.uninstall.before_uninstall"
# after_uninstall = "ecom_custom.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "ecom_custom.utils.before_app_install"
# after_app_install = "ecom_custom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "ecom_custom.utils.before_app_uninstall"
# after_app_uninstall = "ecom_custom.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ecom_custom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Delivery Note": {
		"before_save": "ecom_custom.shopify.tracking.populate_delivery_note_tracking",
		"on_submit": "ecom_custom.shopify.tracking.populate_delivery_note_tracking",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"ecom_custom.tasks.all"
# 	],
# 	"daily": [
# 		"ecom_custom.tasks.daily"
# 	],
# 	"hourly": [
# 		"ecom_custom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ecom_custom.tasks.weekly"
# 	],
# 	"monthly": [
# 		"ecom_custom.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "ecom_custom.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"ecommerce_integrations.shopify.utils.migrate_from_old_connector": "ecom_custom.shopify.overrides.skip_migrate_from_old_connector",
	"ecommerce_integrations.shopify.order.sync_sales_order": "ecom_custom.shopify.order_overrides.sync_sales_order",
}

try:
	from ecommerce_integrations.shopify import order as _base_shopify_order
	from ecom_custom.shopify import order_overrides as _order_overrides
	from ecom_custom.shopify import customer_patch

	_base_shopify_order.sync_sales_order = _order_overrides.sync_sales_order
	_base_shopify_order._fetch_old_orders = _order_overrides.fetch_old_orders_any

	# Ensure Shopify customers always carry a fiscal code placeholder to satisfy Italian validations.
	customer_patch.apply()
except Exception:
	pass
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ecom_custom.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["ecom_custom.utils.before_request"]
# after_request = ["ecom_custom.utils.after_request"]

# Job Events
# ----------
# before_job = ["ecom_custom.utils.before_job"]
# after_job = ["ecom_custom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"ecom_custom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
