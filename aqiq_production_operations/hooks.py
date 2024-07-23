app_name = "aqiq_production_operations"
app_title = "AQIQ Production operations"
app_publisher = "RONOH"
app_description = "Customizations for job card and work order by AQIQ Solutions LTD."
app_email = "ronoelisha625@gmail.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/aqiq_production_operations/css/aqiq_production_operations.css"
# app_include_js = "/assets/aqiq_production_operations/js/aqiq_production_operations.js"

# include js, css files in header of web template
# web_include_css = "/assets/aqiq_production_operations/css/aqiq_production_operations.css"
# web_include_js = "/assets/aqiq_production_operations/js/aqiq_production_operations.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "aqiq_production_operations/public/scss/website"

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
# app_include_icons = "aqiq_production_operations/public/icons.svg"

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
# 	"methods": "aqiq_production_operations.utils.jinja_methods",
# 	"filters": "aqiq_production_operations.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "aqiq_production_operations.install.before_install"
# after_install = "aqiq_production_operations.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "aqiq_production_operations.uninstall.before_uninstall"
# after_uninstall = "aqiq_production_operations.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "aqiq_production_operations.utils.before_app_install"
# after_app_install = "aqiq_production_operations.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "aqiq_production_operations.utils.before_app_uninstall"
# after_app_uninstall = "aqiq_production_operations.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "aqiq_production_operations.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"aqiq_production_operations.tasks.all"
# 	],
# 	"daily": [
# 		"aqiq_production_operations.tasks.daily"
# 	],
# 	"hourly": [
# 		"aqiq_production_operations.tasks.hourly"
# 	],
# 	"weekly": [
# 		"aqiq_production_operations.tasks.weekly"
# 	],
# 	"monthly": [
# 		"aqiq_production_operations.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "aqiq_production_operations.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "aqiq_production_operations.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "aqiq_production_operations.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["aqiq_production_operations.utils.before_request"]
# after_request = ["aqiq_production_operations.utils.after_request"]

# Job Events
# ----------
# before_job = ["aqiq_production_operations.utils.before_job"]
# after_job = ["aqiq_production_operations.utils.after_job"]

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
# 	"aqiq_production_operations.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
    {
        "dt": "Client Script",
        "filters": [
            ["name", "in", ["Workstation", "Job Card Tool","Workstation Custom"]]
        ]
    },
    {
        "dt": "Custom Field",
        "filters": [
            ["dt", "in", ["Work Order", "Job Card", "Workstation"]],
            ["is_system_generated", "=", 0]
        ]
    },
    {
        "dt": "DocType",
        "filters": [
            ["name", "in", ["Job Card Tool","Workstation Employee"]],
            ["custom", "=", 1]
        ]
    },
    {
        "dt": "Print Format",
        "filters": [
            ["doc_type", "in", ["Work Order", "Job Card", "Workstation"]],
            ["standard", "=", "No"]
        ]
    }
]





