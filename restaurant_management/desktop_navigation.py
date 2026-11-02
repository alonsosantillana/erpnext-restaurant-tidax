"""Frappe v16 launcher visibility; reuse existing destination permissions."""

import frappe
from frappe.desk.doctype.dock.dock import get_app_entry_set


def has_app_permission() -> bool:
    """Return whether this System User can open the app's existing destination."""
    user = frappe.session.user
    if not user or user == "Guest":
        return False
    if frappe.get_cached_value("User", user, "user_type") != "System User":
        return False
    if "restaurant_management" not in frappe.get_installed_apps():
        return False
    if not frappe.db.exists("Workspace", "Restaurant Management"):
        return False
    return bool(get_app_entry_set("restaurant_management"))
