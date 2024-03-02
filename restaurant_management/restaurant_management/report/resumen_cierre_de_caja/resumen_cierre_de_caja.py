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
	company = filters.get('company')
	from_d = str(filters.get('report_date_from'))
	to_d = str(filters.get('report_date_to'))

	data = frappe.db.sql("""
				SELECT
					pce.posting_date AS fecha,  
					SUM(pce.grand_total) AS total_ingreso, 
					SUM(rg.gto_total) AS total_gasto,
					(SUM(pce.grand_total) - SUM(rg.gto_total)) as cierre
				FROM
					`tabPOS Closing Entry` as pce
				LEFT JOIN
					`tabResto Gastos` AS rg 
				ON
					pce.posting_date = rg.date_gto
					WHERE
					DATE(pce.posting_date) BETWEEN %s AND %s AND
					pce.docstatus = 1 AND
					rg.docstatus = 1
					  
				GROUP BY pce.posting_date;
			""", (from_d, to_d), as_dict=True)

	return data

def get_columns(filters=None):
    columns = [
		"Fecha:Date:100",
        "Total Ingreso:Float:150",
        "Total Gasto:Float:150",
		"Cierre:Float:150"
    ]

    return columns
