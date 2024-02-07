from __future__ import unicode_literals

import frappe
from datetime import datetime

import json
import frappe.utils
from frappe import _, qb
from frappe.contacts.doctype.address.address import get_company_address
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.query_builder.functions import Sum
from frappe.utils import add_days, cint, cstr, flt, get_link_to_form, getdate, nowdate, strip_html

from erpnext.accounts.doctype.sales_invoice.sales_invoice import (
	unlink_inter_company_doc,
	update_linked_doc,
	validate_inter_company_party,
)
from erpnext.accounts.party import get_party_account
from erpnext.controllers.selling_controller import SellingController
from erpnext.manufacturing.doctype.blanket_order.blanket_order import (
	validate_against_blanket_order,
)
from erpnext.manufacturing.doctype.production_plan.production_plan import (
	get_items_for_material_requests,
)
from erpnext.selling.doctype.customer.customer import check_credit_limit
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.stock.get_item_details import get_default_bom, get_price_list_rate
from erpnext.stock.stock_balance import get_reserved_qty, update_bin_qty

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}

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

    ordenes = frappe.db.sql(f"""
    SELECT 
    taor.name, 
    taor.table_description, 
    taor.room_description, 
    oei.item_code AS item_code, 
    oei.item_name AS item_name, 
    oei.qty, 
    oei.notes,
    LEFT(oei.ordered_time, 19) as ordered_time,
    CONCAT(
    taor.name,
    CASE
    WHEN DENSE_RANK() OVER (PARTITION BY taor.name ORDER BY LEFT(oei.ordered_time, 16)) > 0
    THEN CONCAT(
    '-',
    DENSE_RANK() OVER (PARTITION BY taor.name ORDER BY LEFT(oei.ordered_time, 16))
    )
    ELSE ''
    END
    ) AS sub_name
    FROM 
    `tabTable Order` AS taor 
    INNER JOIN
    `tabOrder Entry Item` AS oei
    ON DATE(taor.creation) BETWEEN '{hoy}' AND '{hoy}' 
    AND taor.name = oei.parent
    AND taor.status != 'Invoiced' 
    AND (oei.status != 'Attending' AND oei.status != 'Completed')
    GROUP BY 
    taor.name, 
    taor.table_description, 
    taor.room_description, 
    oei.item_code, 
    oei.item_name, 
    oei.qty, 
    oei.notes, 
    oei.ordered_time
    ORDER BY 
    oei.ordered_time, sub_name ASC, taor.name ASC;
    """, as_dict=True)

    return ordenes



@frappe.whitelist()
def update_comanda_atendida(order_name, ordered_time):
    try:
        # Convertir la cadena a un objeto de fecha y hora para manejar la comparación adecuadamente
        ordered_time_dt = datetime.strptime(ordered_time, "%Y-%m-%d %H:%M:%S")
        # ordered_time_dt = datetime.strptime(ordered_time, "%Y-%m-%d %H:%M")

        # Obtener datos de la base de datos sin tener en cuenta milisegundos
        # query = f"""
        #     SELECT *
        #     FROM `tabOrder Entry Item`
        #     WHERE `parent` = '{order_name}'
        #     AND DATE_FORMAT(`ordered_time`, '%Y-%m-%d %H:%i:%s') = '{ordered_time_dt.strftime('%Y-%m-%d %H:%M:%S')}'
        # """
        query = f"""
            SELECT *
            FROM `tabOrder Entry Item`
            WHERE `parent` = '{order_name}'
            AND DATE_FORMAT(`ordered_time`, '%Y-%m-%d %H:%i') = '{ordered_time_dt.strftime('%Y-%m-%d %H:%M')}'
        """

        order_entry_items = frappe.db.sql(query, as_dict=True)
        
        order_table = frappe.get_all("Table Order", filters={"name": order_name}, fields=["creation"])
        fecha_ingresada = order_table[0].get("creation")

        # Obtén la fecha y hora actual
        fecha_actual = datetime.now()

        # Convierte la fecha ingresada a un objeto datetime si aún no lo es
        if not isinstance(fecha_ingresada, datetime):
            fecha_ingresada = datetime.strptime(fecha_ingresada, "%Y-%m-%d %H:%M:%S")
            # fecha_ingresada = datetime.strptime(fecha_ingresada, "%Y-%m-%d %H:%M")

        # Calcula la diferencia de tiempo en minutos
        diferencia_en_minutos = (fecha_actual - fecha_ingresada).total_seconds() / 60.0

        if order_entry_items:
            for item in order_entry_items:
                order_entry_item = frappe.get_doc("Order Entry Item", item['name'])
                if(order_entry_item.ordered_finish == 0 and order_entry_item.status == "Sent"):
                    order_entry_item.ordered_finish = int(diferencia_en_minutos)
                # Actualiza el valor de la columna "status" a "Completed"
                order_entry_item.status = "Completed"
                # Guarda los cambios en la base de datos
                order_entry_item.save()

            frappe.db.commit()

            return "Éxito: Las órdenes han sido marcadas como 'Atendidas'."

        else:
            return "Error: No se encontraron órdenes correspondientes."

    except Exception as e:
        frappe.log_error(f"Error al actualizar las órdenes: {str(e)}")
        return "Error: No se pudieron actualizar las órdenes."
    

@frappe.whitelist()
def make_pos_invoice(source_name, target_doc=None, ignore_permissions=False):
	def postprocess(source, target):
		set_missing_values(source, target)
		# Get the advance paid Journal Entries in Sales Invoice Advance
		if target.get("allocate_advances_automatically"):
			target.set_advances()

	def set_missing_values(source, target):
		target.flags.ignore_permissions = True
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")

		if source.company_address:
			target.update({"company_address": source.company_address})
		else:
			# set company address
			target.update(get_company_address(target.company))

		if target.company_address:
			target.update(get_fetch_values("POS Invoice", "company_address", target.company_address))

		# set the redeem loyalty points if provided via shopping cart
		if source.loyalty_points and source.order_type == "Shopping Cart":
			target.redeem_loyalty_points = 1

		target.debit_to = get_party_account("Customer", source.customer, source.company)

	def update_item(source, target, source_parent):
		target.amount = flt(source.amount) - flt(source.billed_amt)
		target.base_amount = target.amount * flt(source_parent.conversion_rate)
		target.qty = (
			target.amount / flt(source.rate)
			if (source.rate and source.billed_amt)
			else source.qty - source.returned_qty
		)

		if source_parent.project:
			target.cost_center = frappe.db.get_value("Project", source_parent.project, "cost_center")
		if target.item_code:
			item = get_item_defaults(target.item_code, source_parent.company)
			item_group = get_item_group_defaults(target.item_code, source_parent.company)
			cost_center = item.get("selling_cost_center") or item_group.get("selling_cost_center")

			if cost_center:
				target.cost_center = cost_center

	doclist = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {
				"doctype": "Sales Invoice",
				"field_map": {
					"party_account_currency": "party_account_currency",
					"payment_terms_template": "payment_terms_template",
				},
				"field_no_map": ["payment_terms_template"],
				"validation": {"docstatus": ["=", 1]},
			},
			"Sales Order Item": {
				"doctype": "Sales Invoice Item",
				"field_map": {
					"name": "so_detail",
					"parent": "sales_order",
				},
				"postprocess": update_item,
				"condition": lambda doc: doc.qty
				and (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
			},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
			"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
		},
		target_doc,
		postprocess,
		ignore_permissions=ignore_permissions,
	)

	automatically_fetch_payment_terms = cint(
		frappe.db.get_single_value("Accounts Settings", "automatically_fetch_payment_terms")
	)
	if automatically_fetch_payment_terms:
		doclist.set_payment_schedule()

	doclist.set_onload("ignore_price_list", True)

	return doclist


@frappe.whitelist()
def make_material_request(source_name, target_doc=None):
	requested_item_qty = get_requested_item_qty(source_name)

	def update_item(source, target, source_parent):
		# qty is for packed items, because packed items don't have stock_qty field
		qty = source.get("qty")
		target.project = source_parent.project
		target.qty = qty - requested_item_qty.get(source.name, 0) - flt(source.get("delivered_qty"))
		target.stock_qty = flt(target.qty) * flt(target.conversion_factor)

		args = target.as_dict().copy()
		args.update(
			{
				"company": source_parent.get("company"),
				"price_list": frappe.db.get_single_value("Buying Settings", "buying_price_list"),
				"currency": source_parent.get("currency"),
				"conversion_rate": source_parent.get("conversion_rate"),
			}
		)

		target.rate = flt(
			get_price_list_rate(args=args, item_doc=frappe.get_cached_doc("Item", target.item_code)).get(
				"price_list_rate"
			)
		)
		target.amount = target.qty * target.rate

	doc = get_mapped_doc(
		"POS Invoice",
		source_name,
		{
			"POS Invoice": {"doctype": "Material Request", "validation": {"docstatus": ["=", 1]}},
			"Packed Item": {
				"doctype": "Material Request Item",
				"field_map": {"parent": "sales_order", "uom": "stock_uom"},
				"postprocess": update_item,
			},
			"POS Invoice Item": {
				"doctype": "Material Request Item",
				"field_map": {"name": "pos_invoice_item", "parent": "pos_invoice"},
				"condition": lambda doc: not frappe.db.exists("Product Bundle", doc.item_code)
				and (doc.stock_qty - flt(doc.get("delivered_qty"))) > requested_item_qty.get(doc.name, 0),
				"postprocess": update_item,
			},
		},
		target_doc,
	)

	return doc

def get_requested_item_qty(sales_order):
	return frappe._dict(
		frappe.db.sql(
			"""
		select pos_invoice_item, sum(qty)
		from `tabMaterial Request Item`
		where docstatus = 1
			and pos_invoice = %s
		group by pos_invoice_item
	""",
			sales_order,
		)
	)


