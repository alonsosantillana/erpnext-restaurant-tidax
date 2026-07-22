import frappe


def execute():
    if not frappe.db.has_column("Table Order", "service_type"):
        return

    frappe.db.sql(
        """
        UPDATE `tabTable Order`
        SET `service_type` = %s
        WHERE COALESCE(`service_type`, '') = ''
        """,
        ("Dine In",),
    )
