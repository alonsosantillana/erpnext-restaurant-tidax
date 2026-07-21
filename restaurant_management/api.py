from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import getdate
import requests

SUCCESS = 200
NOT_FOUND = 400
DOCUMENT_METHODS = {
    "Restaurant Object": {
        "_delete",
        "add_object",
        "add_order",
        "commands_food",
        "get_objects",
        "orders_list",
        "set_status_command",
        "set_style",
    },
    "Table Order": {
        "_delete",
        "delete_item",
        "divide",
        "divide_template",
        "get_items",
        "make_invoice",
        "push_item",
        "send",
        "transfer",
    },
}

READ_ONLY_DOCUMENT_METHODS = {
    ("Restaurant Object", "commands_food"),
    ("Restaurant Object", "get_objects"),
    ("Restaurant Object", "orders_list"),
    ("Table Order", "divide_template"),
    ("Table Order", "get_items"),
}

DELETE_DOCUMENT_METHODS = {
    ("Restaurant Object", "_delete"),
    ("Table Order", "_delete"),
}


def _require_authenticated_user():
    if frappe.session.user == "Guest":
        frappe.throw(_("Authentication required"), frappe.AuthenticationError)


@frappe.whitelist()
def call(model, name, method, args=None):
    """Call an explicitly supported restaurant document action."""
    _require_authenticated_user()

    if method not in DOCUMENT_METHODS.get(model, set()):
        frappe.throw(_("Unsupported restaurant operation"), frappe.PermissionError)

    doc = frappe.get_doc(model, name)
    if (model, method) in READ_ONLY_DOCUMENT_METHODS:
        permission_type = "read"
    elif (model, method) in DELETE_DOCUMENT_METHODS:
        permission_type = "delete"
    else:
        permission_type = "write"
    doc.check_permission(permission_type)

    parsed_args = frappe.parse_json(args) if args else {}
    if not isinstance(parsed_args, dict):
        frappe.throw(_("Operation arguments must be an object"))

    action = getattr(doc, method)
    if callable(action):
        return action(**parsed_args)

    if parsed_args:
        frappe.throw(_("This restaurant operation does not accept arguments"))

    return action


@frappe.whitelist()
def validate_link(value=None, options=None, fetch=None):
    """Validate a Link value and return only permitted fields."""
    _require_authenticated_user()

    if not options or options in {"null", "undefined"}:
        return "Ok"

    if not frappe.has_permission(options, "read"):
        frappe.throw(_("Not permitted to read {0}").format(options), frappe.PermissionError)

    meta = frappe.get_meta(options)
    fetch_fields = [field.strip() for field in (fetch or "").split(",") if field.strip()]
    invalid_fields = [field for field in fetch_fields if field != "name" and not meta.has_field(field)]
    if invalid_fields:
        frappe.throw(_("Invalid fetch fields: {0}").format(", ".join(invalid_fields)))

    permitted = frappe.get_list(options, filters={"name": value}, fields=["name"], limit_page_length=1)
    if not permitted:
        return None

    if fetch_fields:
        frappe.response["fetch_values"] = list(
            frappe.db.get_value(options, value, fetch_fields) or []
        )

    frappe.response["valid_value"] = value
    return "Ok"


@frappe.whitelist()
def get_posinv_summary(from_date, to_date):
    # Convierte las fechas de cadena a objetos date
    desde_fecha = getdate(from_date)
    hasta_fecha = getdate(to_date)

    # Lógica para obtener documentos en el rango de fechas
    documentos = frappe.get_all(
        "POS Invoice",
        filters={
            "posting_date": ["between", [desde_fecha, hasta_fecha]]
        },
        fields=["posting_date", "name", "docstatus", "status", "customer", "customer_name", 
                "tax_id", "address_display", "currency", "net_total", "total_taxes_and_charges", "grand_total", "total", "total_amount_discount_lines",
                "additional_discount_percentage", "discount_amount", "codigo_comprobante", "tipo_comprobante", "comprobante_electronico_manual",
                "codigo_Qr_sunat", "codigo_hash_sunat", "enlace_pdf"]
    )

    response = get_response(documentos)
    return response

@frappe.whitelist()
def get_posinv_paid(from_date, to_date):
    # Convierte las fechas de cadena a objetos date
    desde_fecha = getdate(from_date)
    hasta_fecha = getdate(to_date)

    pagos = frappe.db.sql(f"""SELECT sip.parent, sip.docstatus, sip.mode_of_payment, sip.amount FROM `tabPOS Invoice` as pi INNER JOIN
                                `tabSales Invoice Payment` as sip on pi.name = sip.parent
                                WHERE pi.posting_date BETWEEN %s AND %s
                                ORDER BY sip.parent, sip.idx asc""", (desde_fecha, hasta_fecha), as_dict=True)
                                
    response = get_response(pagos)
    return response

@frappe.whitelist()
def get_posinv_items(from_date, to_date):
    # Convierte las fechas de cadena a objetos date
    desde_fecha = getdate(from_date)
    hasta_fecha = getdate(to_date)

    productos = frappe.db.sql(f"""SELECT pii.parent, pii.docstatus, pii.item_code, pii.item_name, pii.item_group, 
                                    pii.qty, pii.stock_uom, pii.price_list_rate, pii.base_rate, pii.amount, pii.base_net_rate, pii.base_net_amount, 
                                    pii.discount_percentage, pii.discount_amount FROM `tabPOS Invoice` as pi INNER JOIN
                                    `tabPOS Invoice Item` as pii on pi.name = pii.parent
                                    WHERE pi.posting_date BETWEEN %s AND %s
                                    ORDER BY pii.parent, pii.idx asc""", (desde_fecha, hasta_fecha), as_dict=True)
                                    
    response = get_response(productos)
    return response

@frappe.whitelist()
def get_response(busqueda=None):
    if(busqueda):
        # status_code = SUCCESS
        body = busqueda
    else:
        # status_code = NOT_FOUND
        body = "No existe lo buscado"
    
    response = dict(
        # status_code = status_code,
        body = body
    )
    return response
