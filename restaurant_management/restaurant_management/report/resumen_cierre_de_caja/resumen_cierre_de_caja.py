# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt

# import frappe

from __future__ import unicode_literals
from datetime import date
from erpnext.setup.doctype import company
from frappe import _
import frappe
import os

def execute_legacy(filters=None):
	return get_columns(filters), get_data(filters)

def get_data(filters):
	company = filters.get('company')
	from_d = str(filters.get('report_date_from'))
	to_d = str(filters.get('report_date_to'))

	data = frappe.db.sql("""
				SELECT
					pce.posting_date AS fecha,  
					SUM(pce.grand_total) AS total_ingreso,
					SUM(pced.expected_amount) AS propinas,
					(SELECT SUM(gto_total) FROM `tabResto Gastos` WHERE DATE(pce.posting_date) = DATE(date_gto) AND docstatus = 1) as total_gastos,
					(SUM(pce.grand_total) + SUM(pced.expected_amount) - (SELECT SUM(gto_total) FROM `tabResto Gastos` WHERE DATE(pce.posting_date) = DATE(date_gto) AND docstatus = 1)) as cierre
				FROM `tabPOS Closing Entry` as pce
				INNER JOIN
					`tabPOS Closing Entry Detail` AS pced ON pce.name = pced.parent
				WHERE
					DATE(pce.posting_date) BETWEEN %s AND %s
					AND pce.docstatus = 1
					AND pced.mode_of_payment = 'Propinas'
				GROUP BY
					pce.posting_date;
			""", (from_d, to_d), as_dict=True)

	return data

def get_columns(filters=None):
    columns = [
		"Fecha:Date:100",
        "Total Ingreso:Float:150",
		"Propinas:Float:150",
        "Total Gastos:Float:150",
		"Cierre:Float:150"
    ]

    return columns


def execute(filters=None):
    filters = frappe._dict(filters or {})
    company = filters.get("company")
    if not company:
        frappe.throw(_("Company is required"))
    if not frappe.has_permission("Company", "read", doc=company):
        frappe.throw(
            _("No tiene permiso para consultar la empresa {0}").format(company),
            frappe.PermissionError,
        )

    data = frappe.db.sql(
        """
        SELECT
            pce.posting_date AS fecha,
            SUM(pce.grand_total) AS total_ingreso,
            COALESCE((
                SELECT SUM(tip.amount)
                FROM `tabRestaurant Tip` tip
                WHERE tip.company = pce.company
                  AND tip.posting_date = pce.posting_date
                  AND tip.status != 'Cancelled'
            ), 0) AS propinas,
            COALESCE((
                SELECT SUM(gasto.gto_total)
                FROM `tabResto Gastos` gasto
                WHERE gasto.date_gto = pce.posting_date
                  AND gasto.docstatus = 1
            ), 0) AS total_gastos
        FROM `tabPOS Closing Entry` pce
        WHERE pce.company = %(company)s
          AND pce.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND pce.docstatus = 1
        GROUP BY pce.company, pce.posting_date
        ORDER BY pce.posting_date DESC
        """,
        {
            "company": company,
            "from_date": filters.get("report_date_from"),
            "to_date": filters.get("report_date_to"),
        },
        as_dict=True,
    )
    for row in data:
        row.cierre = (
            frappe.utils.flt(row.total_ingreso)
            + frappe.utils.flt(row.propinas)
            - frappe.utils.flt(row.total_gastos)
        )

    columns = [
        {"fieldname": "fecha", "label": _("Fecha"), "fieldtype": "Date", "width": 100},
        {"fieldname": "total_ingreso", "label": _("Total Ingreso"), "fieldtype": "Currency", "width": 150},
        {"fieldname": "propinas", "label": _("Propinas"), "fieldtype": "Currency", "width": 150},
        {"fieldname": "total_gastos", "label": _("Total Gastos"), "fieldtype": "Currency", "width": 150},
        {"fieldname": "cierre", "label": _("Cierre"), "fieldtype": "Currency", "width": 150},
    ]
    return columns, data
