from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import getdate
import requests

SUCCESS = 200
NOT_FOUND = 400

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
