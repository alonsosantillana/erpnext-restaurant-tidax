from __future__ import unicode_literals
from pathlib import Path

import frappe
from frappe.modules.import_file import import_file_by_path

docs = {
    "POS Profile User": dict(
        allow_restaurant_payment=dict(
            label="Puede cobrar",
            fieldtype="Check",
            default="0",
            insert_after="user",
            in_list_view=1,
            description=(
                "Permite al mozo usar el botón Pagar en sus propias órdenes."
            ),
        ),
        allow_restaurant_payment_for_others=dict(
            label="Cobrar otros pedidos",
            fieldtype="Check",
            default="0",
            insert_after="allow_restaurant_payment",
            depends_on="eval:doc.allow_restaurant_payment",
            in_list_view=1,
            description=(
                "Permite al mozo cobrar órdenes asignadas a otros usuarios."
            ),
        ),
        restaurant_permission=dict(
            label="Restaurant Permission",
            fieldtype="Button",
            options="Restaurant Permission",
            insert_after="allow_restaurant_payment_for_others",
            in_list_view=1,
            read_only=1,
        ),
        parent=dict(label="Parent", fieldtype="Data", hidden=1),
        parenttype=dict(label="Parent Type", fieldtype="Data", hidden=1),
        restaurant_permissions=dict(label="Restaurant Permissions", fieldtype="Table",
                                    options="Restaurant Permission", hidden=1, insert_after="restaurant_permission"),
    ),
    "POS Profile": dict(
        posa_tax_inclusive=dict(
            label="Tax Inclusive", fieldtype="Check", insert_after="tax_category", default="1")
    ),
    "POS Invoice": dict(
        restaurant_pos_opening_entry=dict(
            label="Restaurant POS Opening Entry", fieldtype="Link", options="POS Opening Entry",
            insert_after="pos_profile", read_only=1, hidden=1, no_copy=1, search_index=1,
        ),
        update_stock=dict(
            label="Actualiza inventario",
            fieldtype="Check",
            insert_after="restaurant_pos_opening_entry",
            default="0",
            read_only=1,
            no_copy=1,
            in_standard_filter=1,
            description=(
                "Indica si la Factura POS generó movimientos de inventario. "
                "El valor se controla desde Restaurant Company Settings."
            ),
        ),
        restaurant_electronic_status=dict(
            label="Estado de emisión restaurante",
            fieldtype="Select",
            options="\nQueued\nSending\nAccepted\nRetry Required\nRejected",
            insert_after="update_stock",
            read_only=1,
            no_copy=1,
            in_standard_filter=1,
            description="Estado recuperable del envío electrónico iniciado desde Restaurant Manage.",
        ),
        restaurant_electronic_attempts=dict(
            label="Intentos de emisión restaurante",
            fieldtype="Int",
            insert_after="restaurant_electronic_status",
            default="0",
            read_only=1,
            no_copy=1,
        ),
        restaurant_electronic_last_attempt=dict(
            label="Último intento de emisión restaurante",
            fieldtype="Datetime",
            insert_after="restaurant_electronic_attempts",
            read_only=1,
            no_copy=1,
        ),
        restaurant_electronic_last_error=dict(
            label="Último error de emisión restaurante",
            fieldtype="Small Text",
            insert_after="restaurant_electronic_last_attempt",
            read_only=1,
            no_copy=1,
        ),
    ),
    "POS Invoice Item": dict(
        identifier=dict(label="Identifier", fieldtype="Data"),
        restaurant_material_request=dict(
            label="Restaurant Material Request", fieldtype="Link", options="Material Request",
            insert_after="identifier", read_only=1, hidden=1, no_copy=1,
        ),
        restaurant_material_request_item=dict(
            label="Restaurant Material Request Item", fieldtype="Data",
            insert_after="restaurant_material_request", read_only=1, hidden=1, no_copy=1,
        ),
    ),
    "Sales Invoice Item": dict(
        identifier=dict(label="Identifier", fieldtype="Data"),
    ),
    "Item": dict(
        custom_restaurant_preparation_time=dict(
            label="Restaurant Preparation Time (min)",
            fieldtype="Float",
            insert_after="item_group",
            non_negative=1,
            precision="2",
        ),
    ),
    "Item Group": dict(
        custom_restaurant_preparation_time=dict(
            label="Restaurant Preparation Time (min)",
            fieldtype="Float",
            insert_after="parent_item_group",
            non_negative=1,
            precision="2",
        ),
    ),
    "POS Opening Entry": dict(
        restaurant_naming_series=dict(
            label="POS Opening Series",
            fieldtype="Data",
            insert_after="company",
            read_only=1,
            bold=1,
            no_copy=1,
        ),
    ),
    "POS Closing Entry": dict(
        restaurant_naming_series=dict(
            label="POS Closing Series",
            fieldtype="Data",
            insert_after="company",
            read_only=1,
            bold=1,
            no_copy=1,
        ),
        restaurant_expense_total=dict(
            label="Total Gastos",
            fieldtype="Currency",
            insert_after="total_quantity",
            options="company:company_currency",
            read_only=1,
            bold=1,
            no_copy=1,
            default="0",
        ),
    ),
    "POS Closing Entry Detail": dict(
        restaurant_sales_amount=dict(
            label="Ventas",
            fieldtype="Currency",
            insert_after="opening_amount",
            options="company:company_currency",
            read_only=1,
            in_list_view=1,
            columns=1,
            no_copy=1,
            default="0",
        ),
        restaurant_expense_amount=dict(
            label="Gastos",
            fieldtype="Currency",
            insert_after="restaurant_sales_amount",
            options="company:company_currency",
            read_only=1,
            in_list_view=1,
            columns=1,
            no_copy=1,
            default="0",
        ),
    ),
    "Material Request": dict(
        restaurant_production_section=dict(
            label="Producción de restaurante", fieldtype="Section Break",
            insert_after="set_warehouse", collapsible=1,
        ),
        restaurant_production=dict(
            label="Solicitud de producción Resto", fieldtype="Check",
            insert_after="restaurant_production_section", default="0", read_only=1, no_copy=1,
        ),
        restaurant_pos_profile=dict(
            label="Perfil POS de origen", fieldtype="Link", options="POS Profile",
            insert_after="restaurant_production", read_only=1, no_copy=1,
        ),
        restaurant_from_datetime=dict(
            label="Consumos desde", fieldtype="Datetime", insert_after="restaurant_pos_profile",
            read_only=1, no_copy=1,
        ),
        restaurant_to_datetime=dict(
            label="Consumos hasta", fieldtype="Datetime", insert_after="restaurant_from_datetime",
            read_only=1, no_copy=1,
        ),
        restaurant_production_column=dict(
            fieldtype="Column Break", insert_after="restaurant_to_datetime",
        ),
        restaurant_raw_material_warehouse=dict(
            label="Almacén de materia prima", fieldtype="Link", options="Warehouse",
            insert_after="restaurant_production_column", read_only=1, no_copy=1,
        ),
        restaurant_wip_warehouse=dict(
            label="Almacén en proceso", fieldtype="Link", options="Warehouse",
            insert_after="restaurant_raw_material_warehouse", read_only=1, no_copy=1,
        ),
        restaurant_production_sources_section=dict(
            fieldtype="Section Break", insert_after="restaurant_wip_warehouse",
        ),
        restaurant_production_sources=dict(
            label="Líneas de venta incluidas", fieldtype="Table", options="Restaurant Production Source",
            insert_after="restaurant_production_sources_section", read_only=1, no_copy=1,
        ),
    ),
    "Material Request Item": dict(
        pos_invoice=dict(
            label="POS Invoice", fieldtype="Small Text", insert_after="project", read_only=1,
        ),
        pos_invoice_item=dict(
            label="POS Invoice Item", fieldtype="Data", insert_after="pos_invoice",
            read_only=1, hidden=1, no_copy=1,
        ),
    ),
}

fields_not_needed = ['parent', 'parenttype', 'restaurant_permissions']

OPERATIONAL_ROLES = (
    'resto_admin',
    'resto_cajero',
    'resto_mozo',
    'resto_cocina',
    'resto_delivery',
    'resto_produccion',
)

CUSTOMER_ROLES = (
    'resto_admin',
    'resto_cajero',
    'resto_mozo',
    'resto_delivery',
)

CASHIER_PERMISSION_RULES = {
    # Cash-session documents: the cashier can operate and submit, but cannot
    # cancel or delete accounting documents.
    'POS Profile': ('read', 'select'),
    'POS Opening Entry': ('read', 'select', 'create', 'write', 'submit', 'print', 'report'),
    'POS Closing Entry': ('read', 'select', 'create', 'write', 'submit', 'print', 'report'),
    'POS Invoice': ('read', 'select', 'create', 'write', 'submit', 'print', 'report'),
    'Sales Invoice': ('read', 'select', 'create', 'write', 'submit', 'print', 'report'),
    'Purchase Invoice': ('read', 'select', 'create', 'write', 'submit', 'print', 'report'),
    # Catalogs consulted by restaurant checkout, purchasing, expenses, and cash closing.
    'Item': ('read', 'select'),
    'Item Group': ('read', 'select'),
    'Item Price': ('read', 'select'),
    'Price List': ('read', 'select'),
    'Warehouse': ('read', 'select'),
    'Mode of Payment': ('read', 'select'),
    'Account': ('read', 'select'),
    'Cost Center': ('read', 'select'),
    'Currency': ('read', 'select'),
    'UOM': ('read', 'select'),
    'Stock Settings': ('read',),
    'Buying Settings': ('read',),
    'Supplier': ('read', 'select', 'create', 'write'),
    'Supplier Group': ('read', 'select'),
    'Purchase Order': ('read', 'select'),
    'Purchase Receipt': ('read', 'select'),
    'Purchase Taxes and Charges Template': ('read', 'select'),
    'Tax Category': ('read', 'select'),
    'Item Tax Template': ('read', 'select'),
    'Payment Terms Template': ('read', 'select'),
    'Terms and Conditions': ('read', 'select'),
}

WAITER_PERMISSION_RULES = {
    # Required by the order item editor's item_code Link field.
    'Item': ('read', 'select'),
}

PRODUCTION_PERMISSION_RULES = {
    # Operational production documents. Cancellation and deletion remain
    # reserved for managers so posted stock movements cannot be reversed here.
    'Material Request': ('read', 'select', 'create', 'write', 'submit', 'print', 'report'),
    'Work Order': ('read', 'select', 'create', 'write', 'submit', 'print', 'report'),
    'Stock Entry': ('read', 'select', 'create', 'write', 'submit', 'print', 'report'),
    'Stock Ledger Entry': ('read', 'select', 'report'),
    'Job Card': ('read', 'select', 'create', 'write', 'submit', 'print', 'report'),
    'Serial and Batch Bundle': ('read', 'select', 'create', 'write', 'submit'),
    # Recipes and catalogs used by the restaurant production flow are read-only.
    'BOM': ('read', 'select', 'print', 'report'),
    'Item': ('read', 'select'),
    'Item Group': ('read', 'select'),
    'Warehouse': ('read', 'select'),
    'UOM': ('read', 'select'),
    'Stock Entry Type': ('read', 'select'),
    'Operation': ('read', 'select'),
    'Workstation': ('read', 'select'),
    'Workstation Type': ('read', 'select'),
    'Routing': ('read', 'select'),
    'Project': ('read', 'select'),
    'Cost Center': ('read', 'select'),
    'Account': ('read', 'select'),
    'Currency': ('read', 'select'),
    'POS Profile': ('read', 'select'),
    'Stock Settings': ('read',),
}


PRODUCTION_REPORTS = (
    'Stock Balance',
    'Stock Ledger',
)


def after_install():
    sync_app_metadata()

def after_migrate():
    sync_app_metadata()

def sync_app_metadata():
    set_custom_fields()
    frappe.clear_cache(doctype="POS Invoice")
    from restaurant_management.restaurant_management.pos_closing import (
        backfill_open_restaurant_pos_invoices,
    )

    backfill_open_restaurant_pos_invoices()
    set_pos_closing_grid_properties()
    sync_desk_forms()
    set_custom_scripts()
    set_operational_role_permissions()


def set_pos_closing_grid_properties():
    values = {
        "doctype_or_field": "DocField",
        "doc_type": "POS Closing Entry Detail",
        "field_name": "closing_amount",
        "property": "label",
        "value": "Monto de cierre",
        "property_type": "Data",
        "is_system_generated": 1,
    }
    property_setter_name = frappe.db.exists(
        "Property Setter",
        {
            "doc_type": values["doc_type"],
            "field_name": values["field_name"],
            "property": values["property"],
        },
    )
    property_setter = (
        frappe.get_doc("Property Setter", property_setter_name)
        if property_setter_name
        else frappe.new_doc("Property Setter")
    )
    if not property_setter_name or any(
        property_setter.get(key) != value for key, value in values.items()
    ):
        property_setter.update(values)
        property_setter.flags.ignore_permissions = True
        property_setter.flags.ignore_version = True
        property_setter.save() if property_setter_name else property_setter.insert()

    frappe.clear_cache(doctype="POS Closing Entry Detail")


def set_operational_role_permissions():
    from frappe.permissions import add_permission, update_permission_property

    for role in OPERATIONAL_ROLES:
        if frappe.db.exists('Role', role):
            continue
        role_doc = frappe.get_doc({
            'doctype': 'Role',
            'role_name': role,
            'desk_access': 1,
            'is_custom': 0,
        })
        role_doc.flags.ignore_permissions = True
        role_doc.insert()

    permission_rules = {
        'Company': {
            role: ('read', 'select') for role in OPERATIONAL_ROLES
        },
        'Customer': {
            role: ('read', 'select', 'create') for role in CUSTOMER_ROLES
        },
        'Address': {
            role: ('read', 'select', 'create') for role in CUSTOMER_ROLES
        },
    }
    for doctype, permission_types in CASHIER_PERMISSION_RULES.items():
        permission_rules.setdefault(doctype, {})['resto_cajero'] = permission_types
    for doctype, permission_types in WAITER_PERMISSION_RULES.items():
        permission_rules.setdefault(doctype, {})['resto_mozo'] = permission_types
    for doctype, permission_types in PRODUCTION_PERMISSION_RULES.items():
        permission_rules.setdefault(doctype, {})['resto_produccion'] = permission_types

    for doctype, role_rules in permission_rules.items():
        for role, permission_types in role_rules.items():
            if not frappe.db.exists('Role', role):
                continue

            filters = {
                'parent': doctype,
                'role': role,
                'permlevel': 0,
                'if_owner': 0,
            }
            permission_name = frappe.db.get_value(
                'Custom DocPerm', filters, 'name'
            )
            if not permission_name:
                add_permission(
                    doctype,
                    role,
                    permlevel=0,
                    ptype=permission_types[0],
                )
                permission_name = frappe.db.get_value(
                    'Custom DocPerm', filters, 'name'
                )

            for permission_type in permission_types:
                if not frappe.db.get_value(
                    'Custom DocPerm', permission_name, permission_type
                ):
                    update_permission_property(
                        doctype, role, 0, permission_type, 1
                    )

        frappe.clear_cache(doctype=doctype)

    set_production_report_permissions()


def set_production_report_permissions():
    for report_name in PRODUCTION_REPORTS:
        if not frappe.db.exists('Report', report_name):
            continue

        role_parents = [('Report', report_name)]
        if custom_role := frappe.db.get_value(
            'Custom Role', {'report': report_name}, 'name'
        ):
            role_parents.append(('Custom Role', custom_role))

        for parenttype, parent in role_parents:
            role_filters = {
                'parent': parent,
                'parenttype': parenttype,
                'parentfield': 'roles',
                'role': 'resto_produccion',
            }
            if frappe.db.exists('Has Role', role_filters):
                continue

            frappe.get_doc({
                'doctype': 'Has Role',
                **role_filters,
            }).insert(ignore_permissions=True)

    frappe.clear_cache()


def set_custom_fields():
    for doctype, fields in docs.items():
        for field_name, properties in fields.items():
            if field_name in fields_not_needed:
                continue

            field_id = frappe.db.exists(
                "Custom Field", {"dt": doctype, "fieldname": field_name}
            )
            custom_field = (
                frappe.get_doc("Custom Field", field_id)
                if field_id
                else frappe.new_doc("Custom Field")
            )
            values = {**properties, "dt": doctype, "fieldname": field_name}

            if field_id and all(custom_field.get(key) == value for key, value in values.items()):
                continue

            custom_field.update(values)
            custom_field.flags.ignore_version = True
            custom_field.save() if field_id else custom_field.insert()

    _reorder_custom_fields(
        "Material Request",
        (
            "restaurant_production_section",
            "restaurant_production",
            "restaurant_pos_profile",
            "restaurant_from_datetime",
            "restaurant_to_datetime",
            "restaurant_production_column",
            "restaurant_raw_material_warehouse",
            "restaurant_wip_warehouse",
            "restaurant_production_sources_section",
            "restaurant_production_sources",
        ),
    )


def _reorder_custom_fields(doctype, fieldnames):
    """Keep app-owned custom fields in a deterministic visual order."""
    custom_fields = frappe.get_all(
        "Custom Field",
        filters={"dt": doctype},
        fields=["name", "fieldname", "idx"],
    )
    app_fields = {
        field.fieldname: field
        for field in custom_fields
        if field.fieldname in fieldnames
    }
    last_other_idx = max(
        (field.idx or 0 for field in custom_fields if field.fieldname not in fieldnames),
        default=0,
    )

    for offset, fieldname in enumerate(fieldnames, start=1):
        if field := app_fields.get(fieldname):
            frappe.db.set_value(
                "Custom Field",
                field.name,
                "idx",
                last_other_idx + offset,
                update_modified=False,
            )

    frappe.clear_cache(doctype=doctype)


def sync_desk_forms():
    desk_form_path = Path(frappe.get_app_path(
        "restaurant_management", "restaurant_management", "desk_form"
    ))
    for form_path in sorted(desk_form_path.glob("*/*.json")):
        import_file_by_path(str(form_path), force=True, ignore_version=True)


def set_custom_scripts():
    script_name = frappe.db.get_value(
        "Client Script",
        {
            "dt": "POS Profile",
            "view": "Form",
            "script": ["like", "%get_room_permissions%"],
        },
        "name",
    )
    CS = (
        frappe.get_doc("Client Script", script_name)
        if script_name
        else frappe.new_doc("Client Script")
    )

    CS.set("enabled", 1)
    CS.set("view", "Form")
    CS.set("dt", "POS Profile")
    CS.set("script", """
frappe.ui.form.on("POS Profile", {
    refresh(frm) {
        // Restaurant room access is configured from each saved user row.
    }
});

frappe.ui.form.on("POS Profile User", {
    async restaurant_permission(frm, cdt, cdn) {
        const row = locals[cdt] && locals[cdt][cdn];
        if (!row || row.__islocal) {
            frappe.msgprint(__("Save the POS Profile before assigning room permissions"));
            return;
        }

        const method =
            "restaurant_management.restaurant_management.doctype.restaurant_permission_manage.restaurant_permission_manage";
        const response = await frappe.call({
            method: method + ".get_room_permissions",
            args: { pos_profile_user: cdn },
            freeze: true,
            freeze_message: __("Loading room permissions..."),
        });
        const context = response.message || {};
        const assignedRooms = context.assigned_rooms || [];
        const dialog = new frappe.ui.Dialog({
            title: __("Room Access for {0}", [context.user || ""]),
            size: "large",
            fields: [
                {
                    fieldname: "rooms",
                    fieldtype: "MultiCheck",
                    label: __("Rooms"),
                    columns: 2,
                    select_all: 1,
                    options: (context.rooms || []).map((room) => ({
                        label: room.description
                            ? room.description + " (" + room.name + ")"
                            : room.name,
                        value: room.name,
                        checked: assignedRooms.includes(room.name),
                    })),
                },
            ],
            primary_action_label: __("Save"),
            async primary_action(values) {
                await frappe.call({
                    method: method + ".save_room_permissions",
                    args: {
                        pos_profile_user: cdn,
                        rooms: values.rooms || [],
                    },
                    freeze: true,
                    freeze_message: __("Saving room permissions..."),
                });
                dialog.hide();
                frappe.show_alert({
                    message: __("Room permissions updated"),
                    indicator: "green",
                });
            },
        });
        dialog.show();
    }
});"""
           )
    CS.insert() if CS.is_new() else CS.save()

    legacy_scripts = frappe.get_all(
        "Client Script",
        filters={
            "dt": "POS Profile",
            "view": "Form",
            "script": ["like", "%new DeskForm%"],
        },
        pluck="name",
    )
    for legacy_script in legacy_scripts:
        frappe.db.set_value(
            "Client Script",
            legacy_script,
            "enabled",
            0,
            update_modified=False,
        )
