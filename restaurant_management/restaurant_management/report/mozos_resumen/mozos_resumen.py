# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt

# import frappe


from __future__ import unicode_literals
from datetime import date
from erpnext.setup.doctype import company
from frappe import _
import frappe
import os

def execute(filters=None):
	return get_columns(filters), get_data(filters)

def get_data(filters):
	# print (f"\n\n\n{filters}\n\n\n")
	company = filters.get('company')
	from_d = str(filters.get('report_date_from'))
	to_d = str(filters.get('report_date_to'))
	mozo = filters.get('user_mozo')

	if(mozo):
		data = frappe.db.sql("""
					SELECT
					   `tabTable Order`.`creation` AS fecha, 
						`tabTable Order`.`owner` AS mozo,
						`tabUser`.`full_name` AS nombre,
						COUNT(`tabTable Order`.`name`) AS qty_mesas_atendidas,
						SUM(`tabPOS Invoice`.`grand_total`) AS monto_mesas_atendidas,
						SUM(`tabPOS Invoice`.`total_qty`) AS qty_platos_atendidos
					FROM
						`tabTable Order`
					LEFT JOIN
						`tabPOS Invoice` ON `tabPOS Invoice`.`name` = `tabTable Order`.`link_invoice`
					LEFT JOIN
						`tabUser` ON `tabUser`.`name` = %s
					WHERE
						DATE(`tabTable Order`.`creation`) BETWEEN %s AND %s
						AND `tabTable Order`.`docstatus` = 1
					GROUP BY
						`tabTable Order`.`owner`;
				""", (mozo, from_d, to_d), as_dict=True)
		return data
	else:
		data = frappe.db.sql("""
					SELECT
					   `tabTable Order`.`creation` AS fecha, 
						`tabTable Order`.`owner` AS mozo,
						`tabUser`.`full_name` AS nombre,
						COUNT(`tabTable Order`.`name`) AS qty_mesas_atendidas,
						SUM(`tabPOS Invoice`.`grand_total`) AS monto_mesas_atendidas,
						SUM(`tabPOS Invoice`.`total_qty`) AS qty_platos_atendidos,
					    SUM(`tabTable Order`.`personas`) AS qty_personas_atendidas,
					    (SUM(`tabPOS Invoice`.`grand_total`)/SUM(`tabTable Order`.`personas`)) AS ticket_promedio
					FROM
						`tabTable Order`
					LEFT JOIN
						`tabPOS Invoice` ON `tabPOS Invoice`.`name` = `tabTable Order`.`link_invoice`
					LEFT JOIN
						`tabUser` ON `tabUser`.`name` = `tabTable Order`.`owner`
					WHERE
						DATE(`tabTable Order`.`creation`) BETWEEN %s AND %s
						AND `tabTable Order`.`docstatus` = 1
					GROUP BY
						`tabTable Order`.`owner`;
				""", (from_d, to_d), as_dict=True)

		return data

def get_columns(filters=None):
    columns = [
		"Fecha:Date:100",
        "Mozo:Data:200",
        "Nombre:Data:200",
        "QTY Mesas Atendidas:Data:100",
        "Monto Mesas Atendidas:Data:100",
        "QTY Platos Atendidos:Data:100",
		"QTY Personas Atendidas:Data:100",
		"Ticket Promedio:Data:100"
    ]

    return columns
