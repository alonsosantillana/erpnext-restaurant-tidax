# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	_validate_filters(filters)
	data = get_data(filters)
	if data:
		data.append(_get_total_row(data))
	return get_columns(), data, None, None, None, True


def _validate_filters(filters):
	for fieldname, label in (
		("company", _("Company")),
		("report_date_from", _("From Date")),
		("report_date_to", _("To Date")),
	):
		if not filters.get(fieldname):
			frappe.throw(_("{0} is required").format(label))

	if getdate(filters.report_date_from) > getdate(filters.report_date_to):
		frappe.throw(_("From Date cannot be after To Date"))


def get_data(filters):
	filters = frappe._dict(filters or {})
	filters.invoice_status = "Consolidated"
	filters.pos_invoice_doctype = "POS Invoice"
	filters.payment_parentfield = "payments"
	filters.pos_closing_doctype = "POS Closing Entry"
	filters.pos_transactions_field = "pos_transactions"

	conditions = [
		"invoice.company = %(company)s",
		"invoice.posting_date BETWEEN %(report_date_from)s AND %(report_date_to)s",
		"invoice.docstatus = 1",
		"invoice.status = %(invoice_status)s",
		"invoice.is_return = 0",
		"payment.docstatus = 1",
	]
	if filters.get("pos_profile"):
		conditions.append("invoice.pos_profile = %(pos_profile)s")
	if filters.get("user_cajero"):
		conditions.append("invoice.owner = %(user_cajero)s")
	if filters.get("pos_opening_entry"):
		conditions.append(
			"""
			EXISTS (
				SELECT 1
				FROM `tabPOS Invoice Reference` AS invoice_reference
				INNER JOIN `tabPOS Closing Entry` AS closing_entry
					ON closing_entry.name = invoice_reference.parent
				WHERE
					invoice_reference.pos_invoice = invoice.name
					AND invoice_reference.parenttype = %(pos_closing_doctype)s
					AND invoice_reference.parentfield = %(pos_transactions_field)s
					AND closing_entry.docstatus = 1
					AND closing_entry.pos_opening_entry = %(pos_opening_entry)s
			)
			"""
		)

	data = frappe.db.sql(
		f"""
			SELECT
				invoice.posting_date AS fecha,
				invoice.owner AS cajero,
				user.full_name AS nombre,
				payment.mode_of_payment AS metodo_pago,
				ROUND(SUM(COALESCE(payment.base_amount, payment.amount)), 2) AS monto
			FROM `tabPOS Invoice` AS invoice
			INNER JOIN `tabSales Invoice Payment` AS payment
				ON payment.parent = invoice.name
				AND payment.parenttype = %(pos_invoice_doctype)s
				AND payment.parentfield = %(payment_parentfield)s
			LEFT JOIN `tabUser` AS user ON user.name = invoice.owner
			WHERE {" AND ".join(conditions)}
			GROUP BY
				invoice.posting_date,
				invoice.owner,
				user.full_name,
				payment.mode_of_payment
			ORDER BY
				invoice.posting_date,
				user.full_name,
				payment.mode_of_payment
		""",
		filters,
		as_dict=True,
	)

	currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	for row in data:
		row.currency = currency
	return data


def _get_total_row(data):
	return frappe._dict(
		cajero=_("Total"),
		monto=flt(sum(flt(row.monto) for row in data), 2),
		currency=data[0].currency,
	)


def get_columns(filters=None):
	return [
		{"fieldname": "fecha", "label": _("Fecha"), "fieldtype": "Date", "width": 100},
		{
			"fieldname": "cajero",
			"label": _("Usuario que cobró"),
			"fieldtype": "Data",
			"width": 200,
		},
		{"fieldname": "nombre", "label": _("Nombre"), "fieldtype": "Data", "width": 200},
		{
			"fieldname": "metodo_pago",
			"label": _("Método de pago"),
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"fieldname": "monto",
			"label": _("Monto"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
	]
