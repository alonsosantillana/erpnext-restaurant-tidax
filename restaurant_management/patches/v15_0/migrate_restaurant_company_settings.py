import frappe


SETTINGS_FIELDS = (
    "restricted_to_owner_table",
    "restricted_to_owner_order",
    "multiple_pending_order",
    "color",
    "enable_delivery",
    "enable_pickup",
    "delivery_fee_item",
    "pos_profile",
    "print_format_order",
    "print_format",
    "print_format_ce",
    "serie_factura",
    "serie_boleta",
    "serie_factura_m",
    "serie_boleta_m",
    "to_new_order",
    "to_pay",
    "to_transfer_order",
    "to_change_status_order",
    "no_imprimir",
    "mesas_1",
    "mesas_2",
    "mesas_3",
)


def execute():
    company = _migration_company()
    if not company:
        frappe.log_error(
            "Set a default Company before migrating Restaurant Settings",
            "Restaurant multi-company migration",
        )
        return

    _migrate_settings(company)
    _assign_legacy_objects(company)
    frappe.db.set_single_value("Restaurant Settings", "legacy_company", company)


def _migration_company():
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if company:
        return company

    companies = frappe.get_all("Company", pluck="name", limit_page_length=2)
    return companies[0] if len(companies) == 1 else None


def _migrate_settings(company):
    if frappe.db.exists("Restaurant Company Settings", {"company": company}):
        return

    legacy = frappe.get_single("Restaurant Settings")
    target = frappe.new_doc("Restaurant Company Settings")
    target.company = company
    target.flags.restaurant_settings_migration = True

    for fieldname in SETTINGS_FIELDS:
        value = legacy.get(fieldname)
        if fieldname == "pos_profile" and value:
            if frappe.db.get_value("POS Profile", value, "company") != company:
                continue
        target.set(fieldname, value)

    child_fields = [
        field.fieldname
        for field in frappe.get_meta("Restaurant Exceptions").fields
    ]
    for row in legacy.get("restaurant_exceptions", []):
        target.append(
            "restaurant_exceptions",
            {fieldname: row.get(fieldname) for fieldname in child_fields},
        )

    target.insert(ignore_permissions=True)


def _assign_legacy_objects(company):
    frappe.db.sql(
        """
        UPDATE `tabRestaurant Object`
        SET company = %s
        WHERE company IS NULL OR company = ''
        """,
        company,
    )
