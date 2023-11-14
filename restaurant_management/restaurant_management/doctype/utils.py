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
    ordenes = frappe.db.sql(f"""SELECT taor.name, taor.table_description, taor.room_description, oei.item_code as item_code, oei.item_name as item_name, 
                            oei.qty, oei.notes FROM `tabTable Order` AS taor INNER JOIN
                            `tabOrder Entry Item` AS oei
                            on DATE(taor.creation) between '{hoy}' and '{hoy}' AND taor.name = oei.parent
                            AND taor.status != 'Invoiced' AND (oei.status != 'Attending' AND oei.status != 'Completed')
                            ORDER BY taor.name asc;""", as_dict=True)

    return ordenes

@frappe.whitelist()
def update_comanda_atendida(order_name):
    try:
        # Realiza una búsqueda para obtener todos los registros correspondientes en "Order Entry Item"
        order_entry_items = frappe.get_all("Order Entry Item", filters={"parent": order_name})
        order_table = frappe.get_all("Table Order", filters={"name": order_name}, fields=["creation"])
        fecha_ingresada = order_table[0].get("creation")

        # Obtén la fecha y hora actual
        fecha_actual = datetime.now()

        # Convierte la fecha ingresada a un objeto datetime si aún no lo es
        if not isinstance(fecha_ingresada, datetime):
            fecha_ingresada = datetime.strptime(fecha_ingresada, "%Y-%m-%d %H:%M:%S")

        # Calcula la diferencia de tiempo en minutos
        diferencia_en_minutos = (fecha_actual - fecha_ingresada).total_seconds() / 60.0

        if order_entry_items:
            for item in order_entry_items:
                order_entry_item = frappe.get_doc("Order Entry Item", item['name'])
                # Actualiza el valor de la columna "status" a "Completed"
                order_entry_item.status = "Completed"
                order_entry_item.ordered_finish = int(diferencia_en_minutos)
                # Guarda los cambios en la base de datos
                order_entry_item.save()

            frappe.db.commit()

            return "Éxito: Las órdenes han sido marcadas como 'Atendidas'."

        else:
            return "Error: No se encontraron órdenes correspondientes."

    except Exception as e:
        frappe.log_error(f"Error al actualizar las órdenes: {str(e)}")
        return "Error: No se pudieron actualizar las órdenes."


