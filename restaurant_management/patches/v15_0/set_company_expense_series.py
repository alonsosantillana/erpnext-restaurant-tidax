import frappe

from restaurant_management.restaurant_management.pos_series import (
    EXPENSE_SERIES_FIELD,
    get_default_expense_series,
)


def execute():
    settings_rows = frappe.get_all(
        "Restaurant Company Settings",
        fields=["name", "company", EXPENSE_SERIES_FIELD],
        limit_page_length=0,
    )
    for settings in settings_rows:
        if settings.get(EXPENSE_SERIES_FIELD):
            continue
        frappe.db.set_value(
            "Restaurant Company Settings",
            settings.name,
            EXPENSE_SERIES_FIELD,
            get_default_expense_series(settings.company),
            update_modified=False,
        )
