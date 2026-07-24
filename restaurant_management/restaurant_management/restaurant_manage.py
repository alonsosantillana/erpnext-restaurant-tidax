from __future__ import unicode_literals
import frappe
from frappe import _
from restaurant_management.restaurant_management.company_settings import (
    get_restaurant_settings,
)


def check_exceptions(model, error_message):
    if frappe.session.user == "Administrator":
        return True

    if frappe.has_permission(model["name"], model["action"]):
        has_permission = True

        if model["data"].owner != frappe.session.user or model["short_name"] == "table":
            has_permission = False

            company = model["data"].get("company")
            exceptions = get_restaurant_settings(company=company)
            profile = frappe.db.get_value("User", frappe.session.user, "role_profile_name")
            permissions = [row for row in exceptions.restaurant_exceptions
                           if row.role_profile == profile]

            if model["short_name"] == "order" and not exceptions.restricted_to_owner_order:
                has_permission = True

            if model["short_name"] == "table" and not exceptions.restricted_to_owner_table:
                has_permission = True

            for permission in permissions:
                if model["short_name"] == "order" and exceptions.restricted_to_owner_order:
                    has_permission = permission[f'{model["short_name"]}_{model["action"]}']

                if model["short_name"] == "table" and exceptions.restricted_to_owner_table:
                    has_permission = permission[f'{model["short_name"]}_{model["action"]}']

        if not has_permission:
            frappe.throw(_(error_message))
    else:
        frappe.throw(_("You do not have permissions to update " + model["short_name"]))

    return True
