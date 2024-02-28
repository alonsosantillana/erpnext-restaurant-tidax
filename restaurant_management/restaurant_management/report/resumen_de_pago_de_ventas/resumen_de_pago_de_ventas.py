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
					   `tabPOS Invoice`.`posting_date` AS fecha, 
						`tabPOS Invoice`.`owner` AS cajero,
						`tabUser`.`full_name` AS nombre,
						`tabSales Invoice Payment`.`mode_of_payment` AS metodo_pago,
						SUM(`tabSales Invoice Payment`.`amount`) AS monto
					FROM
						`tabPOS Invoice`
					LEFT JOIN
						`tabSales Invoice Payment` ON  `tabPOS Invoice`.`name` = `tabSales Invoice Payment`.`parent`
					LEFT JOIN
						`tabUser` ON `tabUser`.`name` = %s
					WHERE
						DATE(`tabPOS Invoice`.`posting_date`) BETWEEN %s AND %s
						AND `tabPOS Invoice`.`status` = "Consolidated"
					GROUP BY
						`tabPOS Invoice`.`owner`,
					   	`tabSales Invoice Payment`.`mode_of_payment`;
				""", (mozo, from_d, to_d), as_dict=True)
		return data
	else:
		data = frappe.db.sql("""
					SELECT
					   `tabPOS Invoice`.`posting_date` AS fecha, 
						`tabPOS Invoice`.`owner` AS cajero,
						`tabUser`.`full_name` AS nombre,
						`tabSales Invoice Payment`.`mode_of_payment` AS metodo_pago,
						SUM(`tabSales Invoice Payment`.`amount`) AS monto
					FROM
						`tabPOS Invoice`
					LEFT JOIN
						`tabSales Invoice Payment` ON  `tabPOS Invoice`.`name` = `tabSales Invoice Payment`.`parent`
					LEFT JOIN
						`tabUser` ON `tabUser`.`name` = `tabPOS Invoice`.`owner`
					WHERE
						DATE(`tabPOS Invoice`.`posting_date`) BETWEEN %s AND %s
						AND `tabPOS Invoice`.`status` = "Consolidated"
					GROUP BY
						`tabPOS Invoice`.`owner`,
					   	`tabSales Invoice Payment`.`mode_of_payment`;
				""", (from_d, to_d), as_dict=True)

		return data

def get_columns(filters=None):
    columns = [
		"Fecha:Date:100",
        "Mozo:Data:200",
        "Nombre:Data:200",
        "QTY Mesas Atendidas:Data:100",
        "Monto Mesas Atendidas:Data:100",
        "QTY Platos Atendidos:Data:100"
    ]

    return columns

