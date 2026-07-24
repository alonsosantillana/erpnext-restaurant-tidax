from __future__ import unicode_literals

import frappe
from frappe.model.document import Document

from restaurant_management.restaurant_management.company_settings import (
    RestaurantSettingsMixin,
)


class RestaurantCompanySettings(RestaurantSettingsMixin, Document):
    def validate(self):
        self.validate_restaurant_settings()

    def on_update(self):
        self.publish_settings_update()

    def on_trash(self):
        if frappe.db.exists("Table Order", {"company": self.company}):
            frappe.throw(
                frappe._(
                    "Restaurant settings cannot be deleted while orders exist for {0}"
                ).format(self.company)
            )
