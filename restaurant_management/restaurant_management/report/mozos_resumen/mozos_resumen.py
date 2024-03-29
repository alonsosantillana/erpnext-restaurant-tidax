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
						ROUND(SUM(`tabPOS Invoice`.`grand_total`), 2) AS monto_neto_mesas_atendidas,
					    ROUND(SUM(`tabTable Order`.`amount`), 2) AS monto_bruto_mesas_atendidas,
						SUM(`tabPOS Invoice`.`total_qty`) AS qty_platos_atendidos,
					    SUM(`tabTable Order`.`personas`) AS qty_personas_atendidas,
					    ROUND((SUM(`tabPOS Invoice`.`grand_total`)/(SELECT SUM(grand_total) FROM `tabPOS Invoice` WHERE docstatus = 1 AND 
					   		DATE(posting_date) between %s AND %s))*100, 2) AS porcentaje_ventas_neto,
					    ROUND((SUM(`tabTable Order`.`amount`)/(SELECT SUM(amount) FROM `tabTable Order` WHERE docstatus = 1 AND 
					   		DATE(creation) between %s AND %s))*100, 2) AS porcentaje_ventas_bruto,
					    ROUND(SUM(`tabPOS Invoice`.`grand_total`) / NULLIF(SUM(`tabTable Order`.`personas`), 0), 2) AS ticket_promedio_neto,
					    ROUND(SUM(`tabTable Order`.`amount`) / NULLIF(SUM(`tabTable Order`.`personas`), 0), 2) AS ticket_promedio_bruto
					FROM
						`tabTable Order`
					LEFT JOIN
						`tabPOS Invoice` ON `tabPOS Invoice`.`name` = `tabTable Order`.`link_invoice`
					LEFT JOIN
						`tabUser` ON `tabUser`.`name` = %s
					WHERE
						DATE(`tabTable Order`.`creation`) BETWEEN %s AND %s
					    AND `tabTable Order`.`owner` = %s
						AND `tabTable Order`.`docstatus` = 1
					GROUP BY
						`tabTable Order`.`owner`;
				""", (from_d, to_d, from_d, to_d, mozo, from_d, to_d, mozo), as_dict=True)
		return data
	else:
		data = frappe.db.sql("""
					SELECT
					   `tabTable Order`.`creation` AS fecha, 
						`tabTable Order`.`owner` AS mozo,
						`tabUser`.`full_name` AS nombre,
						COUNT(`tabTable Order`.`name`) AS qty_mesas_atendidas,
						ROUND(SUM(`tabPOS Invoice`.`grand_total`), 2) AS monto_neto_mesas_atendidas,
					    ROUND(SUM(`tabTable Order`.`amount`), 2) AS monto_bruto_mesas_atendidas,
						SUM(`tabPOS Invoice`.`total_qty`) AS qty_platos_atendidos,
					    SUM(`tabTable Order`.`personas`) AS qty_personas_atendidas,
					    ROUND((SUM(`tabPOS Invoice`.`grand_total`)/(SELECT SUM(grand_total) FROM `tabPOS Invoice` WHERE docstatus = 1 AND 
					   		DATE(posting_date) between %s AND %s))*100, 2) AS porcentaje_ventas_neto,
					    ROUND((SUM(`tabTable Order`.`amount`)/(SELECT SUM(amount) FROM `tabTable Order` WHERE docstatus = 1 AND 
					   		DATE(creation) between %s AND %s))*100, 2) AS porcentaje_ventas_bruto,
					    ROUND(SUM(`tabPOS Invoice`.`grand_total`) / NULLIF(SUM(`tabTable Order`.`personas`), 0), 2) AS ticket_promedio_neto,
					    ROUND(SUM(`tabTable Order`.`amount`) / NULLIF(SUM(`tabTable Order`.`personas`), 0), 2) AS ticket_promedio_bruto
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
						`tabTable Order`.`owner`
					ORDER BY
					   	monto_bruto_mesas_atendidas desc;
				""", (from_d, to_d, from_d, to_d, from_d, to_d), as_dict=True)

		return data

def get_columns(filters=None):
    columns = [
		"Fecha:Date:100",
        "Mozo:Data:200",
        "Nombre:Data:100",
        "QTY Mesas Atendidas:Data:100",
        "Monto Neto Mesas Atendidas:Data:100",
		"Monto Bruto Mesas Atendidas:Data:100",
        "QTY Platos Atendidos:Data:100",
		"QTY Personas Atendidas:Data:100",
		"Porcentaje Ventas Neto:Data:100",
		"Porcentaje Ventas Bruto:Data:100",
		"Ticket Promedio Neto:Data:100",
		"Ticket Promedio Bruto:Data:100"
    ]

    return columns
