"""Adopt the standard POS stock flag without changing its column or invoice values."""

import json
from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import delete_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

DOCTYPE = "POS Invoice"
FIELDNAME = "update_stock"
IDENTITY_PROPERTIES = {"fieldname", "fieldtype", "oldfieldname", "oldfieldtype"}
STORAGE_PROPERTIES = {"unique", "search_index", "length", "not_nullable", "is_virtual"}
LAYOUT_TYPES = {"Section Break", "Column Break", "Tab Break", "HTML", "Button"}


def _source_metadata():
    import erpnext

    source = Path(erpnext.__file__).parent / "accounts/doctype/pos_invoice/pos_invoice.json"
    fields = json.loads(source.read_text())["fields"]
    matching = [field for field in fields if field["fieldname"] == FIELDNAME]
    if not matching:
        return None, {}
    if len(matching) != 1 or matching[0]["fieldtype"] != "Check":
        frappe.throw("Native POS Invoice.update_stock must be one Check field; no metadata changed.")
    schema = Path(frappe.__file__).parent / "core/doctype/docfield/docfield.json"
    properties = {
        field["fieldname"]: field
        for field in json.loads(schema.read_text())["fields"]
        if field["fieldtype"] not in LAYOUT_TYPES
        and field["fieldname"] not in IDENTITY_PROPERTIES
    }
    return matching[0], properties


def _normalized(value, fieldtype):
    if fieldtype in {"Check", "Int"}:
        return int(value or 0)
    return "" if value is None else str(value)


def property_plan(native, legacy, setters, schema):
    """Plan missing setters only; existing site overrides always take precedence."""
    existing = {row["property"] for row in setters}
    result = []
    for property_name, definition in schema.items():
        if property_name in STORAGE_PROPERTIES or property_name not in legacy or property_name in existing:
            continue
        fieldtype = definition["fieldtype"]
        native_value = native.get(property_name, definition.get("default"))
        value = legacy[property_name]
        if _normalized(value, fieldtype) != _normalized(native_value, fieldtype):
            result.append((property_name, value, fieldtype))
    return result


def _snapshot_directory():
    workia = Path(frappe.get_site_path("WorkIA")).absolute()
    folder = workia / "native_pos_stock_metadata_compat_v16"
    for path in (folder, workia, *workia.parents):
        if path.is_symlink():
            frappe.throw("Metadata evidence path must not contain symlinks; no metadata changed.")
    if workia.exists() and (not workia.is_dir() or workia.stat().st_mode & 0o077):
        frappe.throw("WorkIA must be a private directory before metadata adoption.")
    workia.mkdir(mode=0o700, exist_ok=True)
    folder.mkdir(mode=0o700, exist_ok=True)
    if not folder.resolve().is_relative_to(workia.resolve()):
        frappe.throw("Metadata evidence escaped WorkIA; no metadata changed.")
    folder.chmod(0o700)
    return folder


def _snapshot(custom_fields, setters, plan):
    """Metadata evidence only, outside app repos and native site backups."""
    layouts = [
        frappe.get_doc("DocType Layout", name).as_dict()
        for name in frappe.get_all(
            "DocType Layout", filters={"document_type": DOCTYPE}, pluck="name"
        )
    ]
    payload = {
        "doctype": DOCTYPE,
        "fieldname": FIELDNAME,
        "custom_fields": custom_fields,
        "property_setters": setters,
        "doctype_layouts": layouts,
        "planned_properties": plan,
        "column_action": "none",
        "invoice_action": "none",
    }
    folder = _snapshot_directory()
    path = folder / ("metadata-before-" + frappe.generate_hash(length=16) + ".json")
    with path.open("x", encoding="utf-8") as stream:
        path.chmod(0o600)
        json.dump(payload, stream, default=str, indent=2)
    return str(path)


def adopt_native_stock_field(properties=None, apply_definition=False):
    native, schema = _source_metadata()
    if native is None:
        return {"native": False, "changed": False}
    standard = frappe.get_all(
        "DocField", filters={"parent": DOCTYPE, "fieldname": FIELDNAME}, fields=["fieldtype"]
    )
    if len(standard) != 1 or standard[0]["fieldtype"] != "Check":
        frappe.throw("Standard POS Invoice.update_stock metadata is not a single Check; no metadata changed.")
    if not frappe.db.has_column(DOCTYPE, FIELDNAME):
        frappe.throw("Native POS Invoice.update_stock column is missing; no metadata changed.")
    custom = frappe.get_all(
        "Custom Field", filters={"dt": DOCTYPE, "fieldname": FIELDNAME}, fields=["*"]
    )
    if len(custom) > 1:
        frappe.throw("Multiple legacy POS stock Custom Fields require review; no metadata changed.")
    if custom:
        field = custom[0]
        if field.get("fieldtype") != "Check" or field.get("is_virtual"):
            frappe.throw("Legacy POS stock field is incompatible; no metadata changed.")
        if _normalized(field.get("default"), "Small Text") != _normalized(native.get("default"), "Small Text"):
            frappe.throw("Legacy POS stock default differs from native; inventory policy review required.")
        for property_name in STORAGE_PROPERTIES:
            definition = schema.get(property_name, {})
            fieldtype = definition.get("fieldtype", "Check")
            expected = native.get(property_name, definition.get("default"))
            if _normalized(field.get(property_name), fieldtype) != _normalized(expected, fieldtype):
                frappe.throw("Legacy POS stock storage attributes differ; no metadata changed.")
        legacy = field
    elif apply_definition:
        legacy = properties or {}
    else:
        return {"native": True, "changed": False}
    setters = frappe.get_all("Property Setter", filters={"doc_type": DOCTYPE}, fields=["*"])
    field_setters = [
        row for row in setters
        if row.get("doctype_or_field") == "DocField" and row.get("field_name") == FIELDNAME
    ]
    if any(row.get("property") == "fieldtype" and row.get("value") != "Check" for row in field_setters):
        frappe.throw("POS stock fieldtype override is incompatible; no metadata changed.")
    plan = property_plan(native, legacy, field_setters, schema)
    if not custom and not plan:
        return {"native": True, "changed": False}
    had_custom = bool(custom)
    evidence = _snapshot(custom, setters, plan)
    for property_name, value, property_type in plan:
        make_property_setter(
            DOCTYPE, FIELDNAME, property_name, value, property_type,
            validate_fields_for_doctype=False,
        )
    if custom:
        delete_custom_fields({DOCTYPE: [FIELDNAME]}, bypass_hooks=True)
    if not frappe.db.has_column(DOCTYPE, FIELDNAME):
        frappe.throw("POS stock column changed unexpectedly; retain maintenance and inspect metadata evidence.")
    return {
        "native": True,
        "changed": True,
        "removed_duplicate": had_custom,
        "created_properties": [row[0] for row in plan],
        "metadata_evidence": evidence,
    }


def before_migrate():
    return adopt_native_stock_field()
