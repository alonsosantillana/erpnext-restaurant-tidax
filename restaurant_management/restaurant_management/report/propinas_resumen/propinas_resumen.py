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
    ]
    values = {
        "company": company,
        "report_date": filters.get("report_date"),
    }
    if not filters.get("include_cancelled"):
        conditions.append("tip.status != 'Cancelled'")
    if filters.get("user_mozo"):
        conditions.append("tip.waiter = %(waiter)s")
        values["waiter"] = filters.user_mozo
    if filters.get("pos_opening_entry"):
        conditions.append(
            "COALESCE(invoice.restaurant_pos_opening_entry, closing.pos_opening_entry) = %(pos_opening_entry)s"
        )
        values["pos_opening_entry"] = filters.pos_opening_entry
    if filters.get("pos_closing_entry"):
        conditions.append("closing.name = %(pos_closing_entry)s")
        values["pos_closing_entry"] = filters.pos_closing_entry

    data = frappe.db.sql(
        """
        SELECT
            tip.name AS name,
            tip.posting_date AS fecha,
            tip.posting_time AS hora,
            tip.waiter AS mozo,
            COALESCE(tip.waiter_name, user.full_name) AS nombre,
            tip.pos_invoice AS comprobante,
            tip.amount AS propinas,
            tip.mode_of_payment AS metodo_de_pago,
            COALESCE(invoice.restaurant_pos_opening_entry, closing.pos_opening_entry) AS apertura_pos,
            opening.period_start_date AS inicio_apertura,
            opening.user AS cajero,
            closing.name AS cierre_pos,
            closing.period_end_date AS fin_cierre,
            tip.status AS estado,
            tip.corrects_tip AS rectifica_propina,
            tip.replaced_by AS rectificada_por,
            tip.cancellation_reason AS motivo_correccion,
            tip.cancelled_by AS anulada_por,
            tip.cancelled_on AS anulada_el,
            tip.collection_journal_entry AS asiento_contable,
            tip.settlement_journal_entry AS asiento_pago,
            tip.settlement_mode_of_payment AS medio_pago_mozo,
            tip.settlement_account AS cuenta_pago,
            tip.settled_by AS pagada_por,
            tip.settled_on AS pagada_el
        FROM `tabRestaurant Tip` tip
        LEFT JOIN `tabUser` user ON user.name = tip.waiter
        LEFT JOIN `tabPOS Invoice` invoice ON invoice.name = tip.pos_invoice
        LEFT JOIN `tabPOS Invoice Reference` invoice_reference
            ON invoice_reference.pos_invoice = tip.pos_invoice
            AND invoice_reference.parenttype = 'POS Closing Entry'
            AND invoice_reference.parentfield = 'pos_transactions'
        LEFT JOIN `tabPOS Closing Entry` closing
            ON closing.name = invoice_reference.parent
            AND closing.docstatus = 1
        LEFT JOIN `tabPOS Opening Entry` opening
            ON opening.name = COALESCE(
                invoice.restaurant_pos_opening_entry,
                closing.pos_opening_entry
            )
        WHERE {conditions}
        ORDER BY tip.posting_time DESC, tip.creation DESC
        """.format(conditions=" AND ".join(conditions)),
        values,
        as_dict=True,
    )

    columns = [
        {"fieldname": "name", "label": _("Registro de propina"), "fieldtype": "Link", "options": "Restaurant Tip", "width": 175},
        {"fieldname": "fecha", "label": _("Fecha"), "fieldtype": "Date", "width": 100},
        {"fieldname": "hora", "label": _("Hora"), "fieldtype": "Time", "width": 90},
        {"fieldname": "mozo", "label": _("Mozo"), "fieldtype": "Link", "options": "User", "width": 190},
        {"fieldname": "nombre", "label": _("Nombre"), "fieldtype": "Data", "width": 180},
        {"fieldname": "comprobante", "label": _("Comprobante"), "fieldtype": "Link", "options": "POS Invoice", "width": 190},
        {"fieldname": "propinas", "label": _("Propina"), "fieldtype": "Currency", "width": 110},
        {"fieldname": "metodo_de_pago", "label": _("Medio de cobro"), "fieldtype": "Link", "options": "Mode of Payment", "width": 140},
        {"fieldname": "apertura_pos", "label": _("Apertura POS"), "fieldtype": "Link", "options": "POS Opening Entry", "width": 190},
        {"fieldname": "inicio_apertura", "label": _("Inicio de caja"), "fieldtype": "Datetime", "width": 155},
        {"fieldname": "cajero", "label": _("Cajero"), "fieldtype": "Link", "options": "User", "width": 190},
        {"fieldname": "cierre_pos", "label": _("Cierre POS"), "fieldtype": "Link", "options": "POS Closing Entry", "width": 190},
        {"fieldname": "fin_cierre", "label": _("Fin de caja"), "fieldtype": "Datetime", "width": 155},
        {"fieldname": "estado", "label": _("Estado"), "fieldtype": "Data", "width": 130},
        {"fieldname": "rectifica_propina", "label": _("Rectifica propina"), "fieldtype": "Link", "options": "Restaurant Tip", "width": 175},
        {"fieldname": "rectificada_por", "label": _("Rectificada por"), "fieldtype": "Link", "options": "Restaurant Tip", "width": 175},
        {"fieldname": "motivo_correccion", "label": _("Motivo de anulación / corrección"), "fieldtype": "Data", "width": 220},
        {"fieldname": "anulada_por", "label": _("Anulada por"), "fieldtype": "Link", "options": "User", "width": 180},
        {"fieldname": "anulada_el", "label": _("Anulada el"), "fieldtype": "Datetime", "width": 155},
        {"fieldname": "medio_pago_mozo", "label": _("Medio de pago al mozo"), "fieldtype": "Link", "options": "Mode of Payment", "width": 165},
        {"fieldname": "cuenta_pago", "label": _("Cuenta de pago"), "fieldtype": "Link", "options": "Account", "width": 210},
        {"fieldname": "pagada_por", "label": _("Pagada por"), "fieldtype": "Link", "options": "User", "width": 180},
        {"fieldname": "pagada_el", "label": _("Pagada el"), "fieldtype": "Datetime", "width": 155},
    ]
    can_read_journal_entry = frappe.has_permission("Journal Entry", "read")
    if can_read_journal_entry:
        columns.extend([{
            "fieldname": "asiento_contable",
            "label": _("Asiento de cobro"),
            "fieldtype": "Link",
            "options": "Journal Entry",
            "width": 190,
        }, {
            "fieldname": "asiento_pago",
            "label": _("Asiento de pago"),
            "fieldtype": "Link",
            "options": "Journal Entry",
            "width": 190,
        }])
    else:
        for row in data:
            row.pop("asiento_contable", None)
            row.pop("asiento_pago", None)
    return columns, data

