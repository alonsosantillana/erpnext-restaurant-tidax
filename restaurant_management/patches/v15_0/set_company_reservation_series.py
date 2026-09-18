import frappe

from restaurant_management.restaurant_management.pos_series import (
    get_default_reservation_series,
)


def execute():
    if not frappe.db.exists("DocType", "Restaurant Company Settings"):
        return
    if not frappe.get_meta("Restaurant Company Settings").has_field(
        "reservation_naming_series"
    ):
        return

    for row in frappe.get_all(
        "Restaurant Company Settings",
        fields=["name", "company", "reservation_naming_series"],
    ):
        if row.reservation_naming_series:
            continue
        frappe.db.set_value(
            "Restaurant Company Settings",
            row.name,
            "reservation_naming_series",
            get_default_reservation_series(row.company),
            update_modified=False,
        )
