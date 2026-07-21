# Copyright (c) 2021, AlphaBit Technology and contributors
# License: GNU General Public License v3

from __future__ import unicode_literals

import frappe
from frappe import _, scrub
from frappe.model.document import Document
from frappe.modules.utils import export_module_json


class DeskForm(Document):
    def validate(self):
        if not self.module:
            self.module = frappe.db.get_value("DocType", self.doc_type, "module")
        if not frappe.flags.in_import:
            self.validate_fields()

    def validate_fields(self):
        from frappe.model import no_value_fields

        meta = frappe.get_meta(self.doc_type)
        missing = []
        for field in self.desk_form_fields:
            if not field.fieldname and field.label:
                field.fieldname = scrub(field.label)
            if (
                field.fieldname
                and field.fieldtype not in no_value_fields
                and not meta.has_field(field.fieldname)
                and not field.extra_field
            ):
                missing.append(field.fieldname)

        if missing:
            frappe.throw(
                _("Following fields are missing in Desk Form {0}: {1}").format(
                    self.title, ", ".join(missing)
                )
            )

    def on_update(self):
        export_module_json(self, bool(self.is_standard), self.module)


def _require_authenticated_user():
    if frappe.session.user == "Guest":
        frappe.throw(_("Authentication required"), frappe.AuthenticationError)


def _get_desk_form(form_name):
    _require_authenticated_user()
    if not form_name:
        frappe.throw(_("Desk Form is required"))

    desk_form = frappe.get_doc("Desk Form", form_name)
    if not (
        frappe.has_permission(desk_form.doc_type, "read")
        or frappe.has_permission(desk_form.doc_type, "create")
    ):
        frappe.throw(_("Not permitted to use this form"), frappe.PermissionError)
    return desk_form


def _validate_exposed_doctype(doctype):
    _require_authenticated_user()
    if not frappe.db.exists("Desk Form", {"doc_type": doctype}):
        frappe.throw(_("DocType is not exposed by a Restaurant Desk Form"), frappe.PermissionError)


def _get_document(doctype, doc_name=None):
    _validate_exposed_doctype(doctype)

    if doc_name and frappe.db.exists(doctype, doc_name):
        doc = frappe.get_doc(doctype, doc_name)
        doc.check_permission("read")
    else:
        if not frappe.has_permission(doctype, "create"):
            frappe.throw(_("Not permitted to create {0}").format(doctype), frappe.PermissionError)
        doc = frappe.new_doc(doctype)
        if doc_name:
            doc.name = doc_name

    doc.new = doc.is_new()
    onload = getattr(doc, "onload", None)
    if callable(onload):
        onload()
    return doc


def _add_table_metadata(result):
    for field in result.desk_form.desk_form_fields:
        if field.fieldtype == "Table":
            field.fields = get_in_list_view_fields(field.options)
            result[field.fieldname] = field.fields


@frappe.whitelist()
def accept(desk_form, data, doc_name=None):
    form = _get_desk_form(desk_form)
    values = frappe.parse_json(data)
    if not isinstance(values, dict):
        frappe.throw(_("Desk Form data must be an object"))

    doctype = form.doc_type
    requested_name = doc_name or values.get("name")
    if requested_name and frappe.db.exists(doctype, requested_name):
        if not form.allow_edit:
            frappe.throw(_("This Desk Form does not allow updates"), frappe.PermissionError)
        doc = frappe.get_doc(doctype, requested_name)
        doc.check_permission("write")
    else:
        if not frappe.has_permission(doctype, "create"):
            frappe.throw(_("Not permitted to create {0}").format(doctype), frappe.PermissionError)
        doc = frappe.new_doc(doctype)

    allowed_fields = {field.fieldname for field in form.desk_form_fields if field.fieldname}
    for fieldname in allowed_fields:
        if fieldname in values:
            doc.set(fieldname, values[fieldname])

    if doc.is_new():
        doc.insert()
    else:
        doc.save()

    return doc


@frappe.whitelist()
def get_form(form_name=None):
    result = frappe._dict(desk_form=_get_desk_form(form_name))
    _add_table_metadata(result)
    return result


@frappe.whitelist()
def get_form_data(form_name=None, doc_name=None):
    result = frappe._dict(desk_form=_get_desk_form(form_name))
    result.doc = _get_document(result.desk_form.doc_type, doc_name)
    _add_table_metadata(result)
    return result


@frappe.whitelist()
def get_doc(doctype, doc_name=None):
    return _get_document(doctype, doc_name)


@frappe.whitelist()
def get_desk_form_filters(desk_form_name):
    desk_form = _get_desk_form(desk_form_name)
    return [field for field in desk_form.desk_form_fields if field.show_in_filter]


@frappe.whitelist()
def get_fetch_values(doctype, txt, searchfield, start=0, page_len=20, filters=None):
    _validate_exposed_doctype(doctype)
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    meta = frappe.get_meta(doctype)
    if searchfield != "name" and not meta.has_field(searchfield):
        frappe.throw(_("Invalid search field"))

    safe_filters = frappe.parse_json(filters) if filters else {}
    if not isinstance(safe_filters, dict):
        frappe.throw(_("Filters must be an object"))
    safe_filters[searchfield] = ["like", f"%{txt or ''}%"]

    return frappe.get_list(
        doctype,
        fields=["name", searchfield],
        filters=safe_filters,
        order_by=searchfield,
        limit_start=max(0, int(start)),
        limit_page_length=min(max(1, int(page_len)), 100),
    )


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_customers(doctype, txt, searchfield, start, page_len, filters):
    """Search permitted customers by ID, name or tax identifier."""
    _require_authenticated_user()
    if doctype != "Customer" or not frappe.has_permission("Customer", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    parsed_filters = frappe.parse_json(filters) if filters else {}
    if not isinstance(parsed_filters, (dict, list)):
        frappe.throw(_("Filters must be an object or a list"))
    if isinstance(parsed_filters, dict):
        parsed_filters.setdefault("disabled", 0)
    else:
        parsed_filters.append(["Customer", "disabled", "!=", 1])

    search_text = f"%{txt or ''}%"
    return frappe.get_list(
        "Customer",
        fields=["name", "customer_name", "tax_id"],
        filters=parsed_filters,
        or_filters=[
            ["Customer", "name", "like", search_text],
            ["Customer", "customer_name", "like", search_text],
            ["Customer", "tax_id", "like", search_text],
        ],
        order_by="customer_name asc, name asc",
        limit_start=max(0, int(start)),
        limit_page_length=min(max(1, int(page_len)), 100),
        as_list=True,
    )


def get_in_list_view_fields(doctype):
    meta = frappe.get_meta(doctype)
    fields = [meta.title_field or "name"]
    if meta.has_field("status"):
        fields.append("status")
    fields.extend(
        field.fieldname
        for field in meta.fields
        if field.in_list_view and field.fieldname not in fields
    )

    def as_field(fieldname):
        if fieldname == "name":
            return {"label": "Name", "fieldname": "name", "fieldtype": "Data"}
        return meta.get_field(fieldname).as_dict()

    return [as_field(fieldname) for fieldname in fields]


@frappe.whitelist()
def get_link_options(desk_form_name, doctype, allow_read_on_all_link_options=False):
    desk_form = _get_desk_form(desk_form_name)
    link_fields = [
        field
        for field in desk_form.desk_form_fields
        if field.fieldtype == "Link" and field.options == doctype
    ]
    if not link_fields or not frappe.has_permission(doctype, "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    allow_all = any(bool(field.allow_read_on_all_link_options) for field in link_fields)
    filters = {} if allow_all else {"owner": frappe.session.user}
    names = frappe.get_list(
        doctype,
        filters=filters,
        fields=["name"],
        order_by="name",
        limit_page_length=500,
    )
    return "\n".join(row.name for row in names)
