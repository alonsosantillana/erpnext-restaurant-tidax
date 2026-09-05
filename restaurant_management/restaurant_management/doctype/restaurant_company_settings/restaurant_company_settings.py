from __future__ import unicode_literals

import frappe
from frappe.model.document import Document

from restaurant_management.restaurant_management.company_settings import (
    RestaurantSettingsMixin,
)
from restaurant_management.restaurant_management.production import (
    validate_company_production_settings,
)


class RestaurantCompanySettings(RestaurantSettingsMixin, Document):
    def validate(self):
        self.validate_restaurant_settings()
        self.validate_default_customer()
        self.validate_print_routes()
        validate_company_production_settings(self)

    def validate_default_customer(self):
        if not self.default_customer:
            return
        customer = frappe.db.get_value(
            "Customer", self.default_customer, ["name", "disabled"], as_dict=True
        )
        if not customer or customer.disabled:
            frappe.throw(frappe._("El cliente predeterminado debe estar habilitado."))

    def validate_print_routes(self):
        enabled_keys = set()
        for route in self.get("print_routes", []):
            if not route.station or not route.print_format or not route.print_type:
                frappe.throw(frappe._("Station, Print Format and Hardware Print Type are required"))
            if route.copies is None or route.copies < 1:
                frappe.throw(frappe._("Print route copies must be at least one"))
            if route.transport_mode == "ESC/POS" and route.document_type not in {"INVOICE", "ACCOUNT"}:
                frappe.throw(frappe._("ESC/POS transport is currently available only for INVOICE and ACCOUNT routes"))
            station = frappe.db.get_value("Restaurant Print Station", route.station, ["company", "enabled"], as_dict=True)
            if not station or station.company != self.company:
                frappe.throw(frappe._("Print station {0} must belong to company {1}").format(route.station, self.company))
            expected_doctype = "POS Invoice" if route.document_type == "INVOICE" else "Table Order"
            if frappe.db.get_value("Print Format", route.print_format, "doc_type") != expected_doctype:
                frappe.throw(frappe._("{0} routes require a {1} Print Format").format(route.document_type, expected_doctype))
            if route.production_center:
                center = frappe.db.get_value("Restaurant Object", route.production_center, ["company", "type"], as_dict=True)
                if not center or center.company != self.company or center.type != "Production Center":
                    frappe.throw(frappe._("Production Center must belong to company {0}").format(self.company))
            if route.enabled:
                key = (route.document_type, route.production_center or "")
                if key in enabled_keys:
                    frappe.throw(frappe._("Only one enabled print route is allowed for {0}").format(route.document_type))
                enabled_keys.add(key)

    def on_update(self):
        self.publish_settings_update()

    def on_trash(self):
        if frappe.db.exists("Table Order", {"company": self.company}):
            frappe.throw(
                frappe._(
                    "Restaurant settings cannot be deleted while orders exist for {0}"
                ).format(self.company)
            )
