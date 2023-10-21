from __future__ import unicode_literals

import frappe
from datetime import datetime

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

@frappe.whitelist()
def get_ordenes_cocina_resumen():
    ordenes = frappe.db.sql(f"""SELECT item_code, item_name, SUM(qty) as qty FROM `tabOrder Entry Item`
                            where (status != 'Attending' AND status != 'Completed')
                            group by item_code;""", as_dict=True)

    return ordenes

@frappe.whitelist()
def get_ordenes_cocina_atendidos():
    hoy = datetime.now()
    hoy = hoy.strftime('%Y-%m-%d')
    ordenes = frappe.db.sql(f"""SELECT oei.item_code as item_code, oei.item_name as item_name, SUM(oei.qty) as qty FROM `tabTable Order` AS taor INNER JOIN
                            `tabOrder Entry Item` AS oei
                            on DATE(taor.creation) between '{hoy}' and '{hoy}' AND taor.name = oei.parent AND oei.status = 'Completed'
                            group by item_code;""", as_dict=True)
    # Invoiced = Totalmente facturado          Completed = Cocina termino de acer el pedido
    return ordenes

@frappe.whitelist()
def get_ordenes_cocina_comandas():
    hoy = datetime.now()
    hoy = hoy.strftime('%Y-%m-%d')
    ordenes = frappe.db.sql(f"""SELECT taor.table_description, taor.room_description, oei.item_code as item_code, oei.item_name as item_name, 
                            oei.qty FROM `tabTable Order` AS taor INNER JOIN
                            `tabOrder Entry Item` AS oei
                            on DATE(taor.creation) between '{hoy}' and '{hoy}' AND taor.name = oei.parent
                            AND taor.status != 'Invoiced' AND (oei.status != 'Attending' AND oei.status != 'Completed')
                            ORDER BY taor.room_description, taor.table_description asc;""", as_dict=True)

    return ordenes
