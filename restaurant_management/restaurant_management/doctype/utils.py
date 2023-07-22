from __future__ import unicode_literals

import frappe

@frappe.whitelist()
def obtener_cliente_por_filtro(filtro):
    # Obtener el cliente según el filtro especificado
    cliente = frappe.get_value("Customer", 
                               fieldname=["name", "customer_name", "customer_type", "territory", "tipo_documento_identidad"],
                               filters={"name":filtro})
    # Devolver el cliente
    return cliente

@frappe.whitelist()
def obtener_res_set(filtro):    
    res_set = frappe.db.sql(f"""SELECT value FROM `tabSingles`
                            where doctype = 'Restaurant Settings' and field = '{filtro}';""", as_dict=True)

    return res_set