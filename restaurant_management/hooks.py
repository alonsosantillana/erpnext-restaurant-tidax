# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from . import __version__ as app_version

app_name = "restaurant_management"
app_title = "Restaurant"
app_publisher = "Quantum Bit Core"
app_description = "Restaurant"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "qubitcore.io@gmail.com"
app_license = "GPL-3.0-only"

required_apps = ["erpnext", "ovenube_peru", "silent_print"]
source_link = "https://github.com/joepa37/restaurant_management"

jinja = {
    "methods": [
        "restaurant_management.thermal_print.qr_svg_data_uri",
    ],
}

sounds = [
    {"name": "chime", "src": "/assets/frappe/sounds/chime.mp3", "volume": 0.7},
]

doc_events = {
    "POS Profile": {
        "on_create": "restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage.set_settings_data",
        "on_update": "restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage.set_settings_data"
    },
    "POS Profile User": {
        "on_create": "restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage.set_settings_data",
        "on_update": "restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage.set_settings_data"
    },
    "POS Opening Entry": {
        "autoname": "restaurant_management.restaurant_management.pos_series.autoname_pos_document",
        "validate": "restaurant_management.restaurant_management.pos_series.validate_pos_document_series",
    },
    "POS Closing Entry": {
        "autoname": "restaurant_management.restaurant_management.pos_series.autoname_pos_document",
        "validate": [
            "restaurant_management.restaurant_management.pos_series.validate_pos_document_series",
            "restaurant_management.restaurant_management.pos_closing_expenses.validate_closing_entry",
        ],
        "before_submit": [
            "restaurant_management.restaurant_management.pos_closing_expenses.validate_no_draft_expenses",
            "restaurant_management.restaurant_management.expense_accounting.validate_expense_accounting_before_closing",
        ],
    },
    "Restaurant Company Settings": {
        "validate": "restaurant_management.restaurant_management.expense_accounting.validate_company_settings_expense_accounting",
    },
    "Resto Gastos": {
        "validate": "restaurant_management.restaurant_management.expense_accounting.validate_expense_accounts",
        "on_submit": "restaurant_management.restaurant_management.expense_accounting.create_expense_journal_entry",
        "on_cancel": "restaurant_management.restaurant_management.expense_accounting.cancel_expense_journal_entry",
    },
    "Journal Entry": {
        "on_cancel": "restaurant_management.restaurant_management.doctype.restaurant_tip.restaurant_tip.restore_tips_for_cancelled_settlement",
    },
    "Material Request": {
        "validate": "restaurant_management.restaurant_management.production.validate_restaurant_production_material_request",
        "on_submit": "restaurant_management.restaurant_management.production.claim_restaurant_production_sources",
        "on_cancel": "restaurant_management.restaurant_management.production.release_restaurant_production_sources",
    },
    "POS Invoice": {
        "before_validate": [
            "restaurant_management.restaurant_management.pos_closing.assign_restaurant_pos_opening",
            "restaurant_management.restaurant_management.production.set_pos_invoice_stock_update",
        ],
        "validate": "restaurant_management.restaurant_management.doctype.table_order.table_order.enforce_restaurant_pos_invoice_currency",
        "on_cancel": "restaurant_management.restaurant_management.doctype.restaurant_tip.restaurant_tip.cancel_tip_for_invoice",
    },
    "Table Order": {
        "autoname": "restaurant_management.restaurant_management.pos_series.autoname_table_order",
    },
}

after_migrate = "restaurant_management.setup.install.after_migrate"
after_install = "restaurant_management.setup.install.after_install"

override_whitelisted_methods = {
    "ovenube_peru.nubefact_integration.facturacion_electronica.update_pos_invoice_ce":
        "restaurant_management.printing.update_pos_invoice_ce_and_queue_print",
    "erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry.get_pos_invoices":
        "restaurant_management.restaurant_management.pos_closing.get_pos_invoices",
}

override_doctype_class = {
    "POS Closing Entry":
        "restaurant_management.restaurant_management.pos_closing.RestaurantPOSClosingEntry",
    "POS Invoice Merge Log":
        "restaurant_management.restaurant_management.pos_invoice_merge.RestaurantPOSInvoiceMergeLog",
}

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    "/assets/restaurant_management/helper/css/desk-form.css",
    "/assets/restaurant_management/helper/css/custom.css",
    "/assets/restaurant_management/helper/css/num-pad.css",
]

fixtures = [
    {
        "dt": "Role",
        "filters": [[
            "name",
            "in",
            [
                "resto_admin",
                "resto_cajero",
                "resto_mozo",
                "resto_cocina",
                "resto_delivery",
                "resto_produccion",
            ],
        ]],
    },
    {
        "dt": "Custom Field",
        "filters": [[
            "name",
            "in",
            [
                "Material Request-clear_item_no_manufacturing",
                "Material Request Item-pos_invoice",
                "Material Request Item-pos_invoice_item",
                "POS Invoice-restaurant_electronic_status",
                "POS Invoice-restaurant_electronic_attempts",
                "POS Invoice-restaurant_electronic_last_attempt",
                "POS Invoice-restaurant_electronic_last_error",
            ],
        ]],
    }
]

app_include_js = [
    "/assets/restaurant_management/helper/js/jshtml-class.js",
    "/assets/restaurant_management/helper/js/num-pad-class.js",
    "/assets/restaurant_management/helper/js/desk-modal.js",
    "/assets/restaurant_management/helper/js/frappe-helper-api.js",
    "/assets/restaurant_management/helper/js/frappe-form-class.js",
    "/assets/restaurant_management/helper/js/desk-form-class.js",
    '/assets/restaurant_management/js/clusterize.min.js',
    '/assets/restaurant_management/js/interact.min.js',
    '/assets/restaurant_management/js/drag.js',
    '/assets/restaurant_management/js/RM.helper.js?v=20260722-2',
    '/assets/restaurant_management/js/object-manage.js',
    '/assets/restaurant_management/js/restaurant_print_indicator.js?v=20260828-2',
]

# include js, css files in header of web template
# web_include_css = "/assets/{app_name}/css/{app_name}.css"
# web_include_js = "/assets/{app_name}/js/{app_name}.js"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# include js in doctype views
doctype_js = {
    "Material Request" : "public/js/material_request.js",
    "Resto Gastos" : "public/js/resto_gastos.js",
    "POS Opening Entry": "public/js/pos_entry_series.js",
    "POS Closing Entry": [
        "public/js/pos_entry_series.js",
        "public/js/pos_closing_expenses.js",
        "public/js/pos_closing_summary.js",
    ],
    "POS Invoice": "public/js/pos_invoice_print.js",
}
# doctype_js = {{"doctype" : "public/js/doctype.js"}}
# doctype_list_js = {{"doctype" : "public/js/doctype_list.js"}}
# doctype_tree_js = {{"doctype" : "public/js/doctype_tree.js"}}
# doctype_calendar_js = {{"doctype" : "public/js/doctype_calendar.js"}}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {{
#	"Role": "home_page"
# }}

# Website user home page (by function)
# get_website_user_home_page = "{app_name}.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "{app_name}.install.before_install"
# after_install = "{app_name}.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "{app_name}.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {{
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }}
#
# has_permission = {{
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {{
# 	"*": {{
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}}
# }}

# Scheduled Tasks
# ---------------

scheduler_events = {
# 	"all": [
# 		"{app_name}.tasks.all"
# 	],
# 	"daily": [
# 		"{app_name}.tasks.daily"
# 	],
# 	"hourly": [
# 		"{app_name}.tasks.hourly"
# 	],
# 	"weekly": [
# 		"{app_name}.tasks.weekly"
# 	]
# 	"monthly": [
# 		"{app_name}.tasks.monthly"
# 	]
    "cron": {
        "*/5 * * * *": [
            "restaurant_management.electronic_invoice.enqueue_pending_pos_invoice_electronic"
        ],
        "0 3 * * *":[
            "restaurant_management.restaurant_management.doctype.utils.update_estado_platos"
        ]
    }
}

# Testing
# -------

# before_tests = "{app_name}.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {{
# 	"frappe.desk.doctype.event.event.get_events": "{app_name}.event.get_events"
# }}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {{
# 	"Task": "{app_name}.task.get_dashboard_data"
# }}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]
