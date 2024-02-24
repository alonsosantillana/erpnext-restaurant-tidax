# Copyright (c) 2024, OVENUBE and contributors
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
	to = str(filters.get('report_date'))
	mozo = filters.get('user_mozo')

	if(mozo):
		data = frappe.db.sql("""SELECT
					    `tabPOS Invoice`.`posting_date` AS fecha,
						`tabTable Order`.`owner` AS codigo_mozo,
						`tabUser`.`full_name` AS mozo,
						`tabPOS Invoice`.`name` AS comprobante,
						`tabSales Invoice Payment`.`amount` AS propina,
						`tabSales Invoice Payment`.`mode_of_payment` AS metodo_pago
					FROM
						`tabTable Order`
					INNER JOIN
						`tabPOS Invoice` ON `tabTable Order`.`link_invoice` = `tabPOS Invoice`.`name`
					INNER JOIN `tabSales Invoice Payment` ON `tabSales Invoice Payment`.`parent` = `tabPOS Invoice`.`name`
					INNER JOIN `tabUser` ON `tabUser`.`name` = `tabTable Order`.`owner`
					WHERE
						`tabSales Invoice Payment`.`mode_of_payment` = 'Propinas'
						AND DATE(`tabPOS Invoice`.`posting_date`) = %s
						AND `tabPOS Invoice`.`docstatus` != 2
					    AND `tabTable Order`.`owner` = %s;""",(to, mozo), as_dict=True)
		return data
	else:
		data = frappe.db.sql("""SELECT
					`tabPOS Invoice`.`posting_date` AS fecha,
					`tabTable Order`.`owner` AS codigo_mozo,
					`tabUser`.`full_name` AS mozo,
					`tabPOS Invoice`.`name` AS comprobante,
					`tabSales Invoice Payment`.`amount` AS propina,
					`tabSales Invoice Payment`.`mode_of_payment` AS metodo_pago
				FROM
					`tabTable Order`
				INNER JOIN
					`tabPOS Invoice` ON `tabTable Order`.`link_invoice` = `tabPOS Invoice`.`name`
				INNER JOIN `tabSales Invoice Payment` ON `tabSales Invoice Payment`.`parent` = `tabPOS Invoice`.`name`
				INNER JOIN `tabUser` ON `tabUser`.`name` = `tabTable Order`.`owner`
				WHERE
					`tabSales Invoice Payment`.`mode_of_payment` = 'Propinas'
					AND DATE(`tabPOS Invoice`.`posting_date`) = %s
					AND `tabPOS Invoice`.`docstatus` != 2;""",(to), as_dict=True)
		return data

def get_columns(filters=None):
    columns = [
		"Fecha:Date:100",
        "Mozo:Data:200",
        "Mozo Nombre:Date:200",
        "Comprobante:Data:200",
        "Propinas:Float:50",
        "Metodo de pago:Data:100",
    ]

    return columns


