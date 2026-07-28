import frappe

from restaurant_management.restaurant_management.pos_series import (
    POS_SERIES_FIELDS,
    get_default_pos_series,
)


def execute():
    settings_rows = frappe.get_all(
        "Restaurant Company Settings",
        fields=["name", "company", *POS_SERIES_FIELDS.values()],
        limit_page_length=0,
    )
    for settings in settings_rows:
        values = {}
        for document_type, fieldname in POS_SERIES_FIELDS.items():
            if not settings.get(fieldname):
                values[fieldname] = get_default_pos_series(
                    settings.company, document_type
                )
        if values:
            frappe.db.set_value(
                "Restaurant Company Settings",
                settings.name,
                values,
                update_modified=False,
            )
