# Copyright (c) 2024, OVENUBE and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from datetime import date
from erpnext.setup.doctype import company
from frappe import _
import frappe
import os

def execute_legacy(filters=None):
	return get_columns(filters), get_data(filters)

def get_data(filters):
	# print (f"\n\n\n{filters}\n\n\n")
	company = filters.get('company')
	to = str(filters.get('report_date'))
	mozo = filters.get('user_mozo')

	if(mozo):
		data = frappe.db.sql("""SELECT
					    `tabPOS Invoice`.`posting_date` AS fecha,
						`tabTable Order`.`owner` AS mozo,
						`tabUser`.`full_name` AS nombre,
						`tabPOS Invoice`.`name` AS comprobante,
						`tabSales Invoice Payment`.`amount` AS propinas,
						`tabSales Invoice Payment`.`mode_of_payment` AS metodo_de_pago
					FROM
						`tabTable Order`
					INNER JOIN
						`tabPOS Invoice` ON `tabTable Order`.`link_invoice` = `tabPOS Invoice`.`name`
					INNER JOIN 
					   	`tabSales Invoice Payment` ON `tabSales Invoice Payment`.`parent` = `tabPOS Invoice`.`name`
					INNER JOIN 
					   	`tabUser` ON `tabUser`.`name` = `tabTable Order`.`owner`
					WHERE
						`tabSales Invoice Payment`.`mode_of_payment` = 'Propinas'
						AND DATE(`tabPOS Invoice`.`posting_date`) = %s
						AND `tabPOS Invoice`.`docstatus` != 2
					    AND `tabTable Order`.`owner` = %s;""",(to, mozo), as_dict=True)
		return data
	else:
		data = frappe.db.sql("""SELECT
					`tabPOS Invoice`.`posting_date` AS fecha,
					`tabTable Order`.`owner` AS mozo,
					`tabUser`.`full_name` AS nombre,
					`tabPOS Invoice`.`name` AS comprobante,
					`tabSales Invoice Payment`.`amount` AS propinas,
					`tabSales Invoice Payment`.`mode_of_payment` AS metodo_de_pago
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
		print(data)
		return data

def get_columns(filters=None):
    columns = [
		"Fecha:Date:100",
        "Mozo:Data:200",
        "Nombre:Data:200",
        "Comprobante:Data:200",
        "Propinas:Data:50",
        "Metodo de pago:Data:100",
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

    conditions = [
        "tip.company = %(company)s",
        "tip.posting_date = %(report_date)s",
        "tip.status != 'Cancelled'",
    ]
    values = {
        "company": company,
        "report_date": filters.get("report_date"),
    }
    if filters.get("user_mozo"):
        conditions.append("tip.waiter = %(waiter)s")
        values["waiter"] = filters.user_mozo

    data = frappe.db.sql(
        """
        SELECT
            tip.posting_date AS fecha,
            tip.waiter AS mozo,
            COALESCE(tip.waiter_name, user.full_name) AS nombre,
            tip.pos_invoice AS comprobante,
            tip.amount AS propinas,
            tip.mode_of_payment AS metodo_de_pago,
            tip.status AS estado,
            tip.collection_journal_entry AS asiento_contable
        FROM `tabRestaurant Tip` tip
        LEFT JOIN `tabUser` user ON user.name = tip.waiter
        WHERE {conditions}
        ORDER BY tip.posting_time DESC, tip.creation DESC
        """.format(conditions=" AND ".join(conditions)),
        values,
        as_dict=True,
    )

    columns = [
        {"fieldname": "fecha", "label": _("Fecha"), "fieldtype": "Date", "width": 100},
        {"fieldname": "mozo", "label": _("Mozo"), "fieldtype": "Link", "options": "User", "width": 190},
        {"fieldname": "nombre", "label": _("Nombre"), "fieldtype": "Data", "width": 180},
        {"fieldname": "comprobante", "label": _("Comprobante"), "fieldtype": "Link", "options": "POS Invoice", "width": 190},
        {"fieldname": "propinas", "label": _("Propina"), "fieldtype": "Currency", "width": 110},
        {"fieldname": "metodo_de_pago", "label": _("Medio de cobro"), "fieldtype": "Link", "options": "Mode of Payment", "width": 140},
        {"fieldname": "estado", "label": _("Estado"), "fieldtype": "Data", "width": 130},
        {"fieldname": "asiento_contable", "label": _("Asiento contable"), "fieldtype": "Link", "options": "Journal Entry", "width": 190},
    ]
    return columns, data

