import frappe


RESTAURANT_ROLES = (
    "resto_admin",
    "resto_cajero",
    "resto_mozo",
    "resto_cocina",
    "resto_delivery",
    "resto_produccion",
)

LEGACY_ROLE_MAP = {
    "Admin Resto": "resto_admin",
    "Cajero": "resto_cajero",
    "Mozo": "resto_mozo",
    "Cocinero": "resto_cocina",
}


def execute():
    for role_name in RESTAURANT_ROLES:
        if frappe.db.exists("Role", role_name):
            continue

        frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
                "is_custom": 0,
            }
        ).insert(ignore_permissions=True)

    for legacy_role, operational_role in LEGACY_ROLE_MAP.items():
        users = frappe.get_all(
            "Has Role",
            filters={"parenttype": "User", "role": legacy_role},
            pluck="parent",
        )
        for user_name in set(users):
            user = frappe.get_doc("User", user_name)
            if operational_role in {row.role for row in user.roles}:
                continue
            user.add_roles(operational_role)
