from __future__ import unicode_literals
from pathlib import Path

import frappe
from frappe.modules.import_file import import_file_by_path

docs = {
    "POS Profile User": dict(
        restaurant_permission=dict(label="Restaurant Permission", fieldtype="Button",
                                   options="Restaurant Permission", insert_after="user", in_list_view=1, read_only=1),
        parent=dict(label="Parent", fieldtype="Data", hidden=1),
        parenttype=dict(label="Parent Type", fieldtype="Data", hidden=1),
        restaurant_permissions=dict(label="Restaurant Permissions", fieldtype="Table",
                                    options="Restaurant Permission", hidden=1, insert_after="restaurant_permission"),
    ),
    "POS Profile": dict(
        posa_tax_inclusive=dict(
            label="Tax Inclusive", fieldtype="Check", insert_after="tax_category", default="1")
    ),
    "POS Invoice Item": dict(
        identifier=dict(label="Identifier", fieldtype="Data"),
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
            no_copy=1,
            default="0",
        ),
    ),
}

fields_not_needed = ['parent', 'parenttype', 'restaurant_permissions']

def after_install():
    sync_app_metadata()

def after_migrate():
    sync_app_metadata()

def sync_app_metadata():
    set_custom_fields()
    sync_desk_forms()
    set_custom_scripts()

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


def sync_desk_forms():
    desk_form_path = Path(frappe.get_app_path(
        "restaurant_management", "restaurant_management", "desk_form"
    ))
    for form_path in sorted(desk_form_path.glob("*/*.json")):
        import_file_by_path(str(form_path), force=True, ignore_version=True)


def set_custom_scripts():
    test_script = frappe.get_value("Client Script", "POS Profile-Form")
    if test_script is None:
        CS = frappe.new_doc("Client Script")
        CS.set("name", "POS Profile-Form")
    else:
        CS = frappe.get_doc("Client Script", test_script)

    CS.set("enabled", 1)
    CS.set("view", "Form")
    CS.set("dt", "POS Profile")
    CS.set("script", """
frappe.ui.form.on('POS Profile', {
    refresh(frm) {
        //refresh
	}
});

frappe.ui.form.on('POS Profile User', {
    restaurant_permission(frm, cdt, cdn) {
        if(cdn.includes('new')){
            frappe.show_alert(__("Save the record before assigning permissions"));
            return;
        }
        
        new DeskForm({
            form_name: 'Restaurant Permission Manage',
            doc_name: cdn,
            callback: (self) => {
                self.hide();
            },
            title: __(`Room Access`),
            field_properties: {
                pos_profile_user: {
                  value: cdn  
                },
                'restaurant_permission.room': {
                    "get_query": () => {
                        return {
                            filters: [
                            ['type', '=', 'Room'],
                            ['company', '=', frm.doc.company]
                            ]
                        }
                    }
                }
            }
        });
    }
});"""
           )
    CS.insert() if test_script is None else CS.save()
