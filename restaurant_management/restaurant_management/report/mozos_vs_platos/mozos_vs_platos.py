# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt

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
						`tabOrder Entry Item`.`item_group` AS grupo_platos,
						`tabOrder Entry Item`.`item_code` AS codigo_platos,
						`tabOrder Entry Item`.`item_name` AS nombre_platos,
						SUM(`tabOrder Entry Item`.`qty`) AS qty_platos_atendidos
					FROM
						`tabTable Order`
					LEFT JOIN
						`tabOrder Entry Item` ON `tabTable Order`.`name` = `tabOrder Entry Item`.`parent`
					LEFT JOIN
						`tabUser` ON `tabUser`.`name` = %s
					WHERE
						DATE(`tabTable Order`.`creation`) BETWEEN %s AND %s
						AND `tabTable Order`.`docstatus` = 1
					GROUP BY
						`tabTable Order`.`owner`,
						`tabOrder Entry Item`.`item_code`                
					HAVING
						qty_platos_atendidos > 0;
				""", (mozo, from_d, to_d), as_dict=True)
		return data
	else:
		data = frappe.db.sql("""
					SELECT
						`tabTable Order`.`creation` AS fecha, 
						`tabTable Order`.`owner` AS mozo,
						`tabUser`.`full_name` AS nombre,
						`tabOrder Entry Item`.`item_group` AS grupo_platos,
						`tabOrder Entry Item`.`item_code` AS codigo_platos,
						`tabOrder Entry Item`.`item_name` AS nombre_platos,
						SUM(`tabOrder Entry Item`.`qty`) AS qty_platos_atendidos
					FROM
						`tabTable Order`
					LEFT JOIN
						`tabOrder Entry Item` ON `tabTable Order`.`name` = `tabOrder Entry Item`.`parent`
					LEFT JOIN
						`tabUser` ON `tabUser`.`name` = `tabTable Order`.`owner`
					WHERE
						DATE(`tabTable Order`.`creation`) BETWEEN %s AND %s
						AND `tabTable Order`.`docstatus` = 1
					GROUP BY
						`tabTable Order`.`owner`,
						`tabOrder Entry Item`.`item_code`                
					HAVING
						qty_platos_atendidos > 0;
				""", (from_d, to_d), as_dict=True)

		return data

def get_columns(filters=None):
    columns = [
		"Fecha:Date:100",
        "Mozo:Data:200",
        "Nombre:Data:200",
        "Grupo Platos:Data:200",
        "Codigo Platos:Data:100",
        "Nombre Platos:Data:200",
		"QTY Platos Atendidos:Data:100"
    ]

    return columns
