# -*- coding: utf-8 -*-
# Copyright (c) 2021, Quantum Bit Core and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from restaurant_management.setup import install
from restaurant_management.restaurant_management.company_settings import (
    RestaurantSettingsMixin,
)


class RestaurantSettings(RestaurantSettingsMixin, Document):
    def validate(self):
        self.validate_restaurant_settings()

    def on_update(self):
        self.publish_settings_update()



@frappe.whitelist()
def reinstall():
    return install.after_install()
