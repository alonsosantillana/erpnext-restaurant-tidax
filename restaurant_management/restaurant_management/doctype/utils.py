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