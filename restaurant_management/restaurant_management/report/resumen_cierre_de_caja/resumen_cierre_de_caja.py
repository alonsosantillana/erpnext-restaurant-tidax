# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	_validate_filters(filters)

	data = _get_data(filters)
	currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	for row in data:
		row.currency = currency
	if data:
		data.append(
			frappe._dict(
				fecha=None,
				total_ingreso=sum(flt(row.total_ingreso) for row in data),
				propinas=sum(flt(row.propinas) for row in data),
				total_gastos=sum(flt(row.total_gastos) for row in data),
				cierre=sum(flt(row.cierre) for row in data),
				currency=currency,
				is_total=1,
			)
		)

	# The report supplies its own total row so Date is not summed by Frappe.
	return _get_columns(), data, None, None, None, True


def _validate_filters(filters):
	company = filters.get("company")
	if not company:
		frappe.throw(_("Company is required"))
	if not frappe.has_permission("Company", "read", doc=company):
		frappe.throw(
			_("No tiene permiso para consultar la empresa {0}").format(company),
			frappe.PermissionError,
		)

	from_date = filters.get("report_date_from")
	to_date = filters.get("report_date_to")
	if not from_date or not to_date:
		frappe.throw(_("From Date and To Date are required"))
	if getdate(from_date) > getdate(to_date):
		frappe.throw(_("From Date cannot be after To Date"))


def _get_data(filters):
	conditions = []
	for fieldname, column in (
		("pos_profile", "closing.pos_profile"),
		("user_cajero", "closing.user"),
		("pos_opening_entry", "closing.pos_opening_entry"),
		("pos_closing_entry", "closing.name"),
	):
		if filters.get(fieldname):
			conditions.append(f"AND {column} = %({fieldname})s")

	return frappe.db.sql(
		f"""
		WITH selected_closings AS (
			SELECT
				closing.name,
				closing.posting_date,
				closing.company,
				closing.pos_profile,
				closing.user,
				closing.pos_opening_entry
			FROM `tabPOS Closing Entry` closing
			WHERE closing.company = %(company)s
			  AND closing.posting_date BETWEEN %(report_date_from)s AND %(report_date_to)s
			  AND closing.docstatus = 1
			  {' '.join(conditions)}
		),
		sales_by_closing AS (
			SELECT
				closing.name AS closing_entry,
				SUM(COALESCE(invoice.base_grand_total, 0)) AS amount
			FROM selected_closings closing
			INNER JOIN `tabPOS Invoice Reference` reference
				ON reference.parent = closing.name
				AND reference.parenttype = 'POS Closing Entry'
				AND reference.parentfield = 'pos_transactions'
			INNER JOIN `tabPOS Invoice` invoice
				ON invoice.name = reference.pos_invoice
				AND invoice.docstatus = 1
			GROUP BY closing.name
		),
		tips_by_closing AS (
			SELECT
				closing.name AS closing_entry,
				SUM(COALESCE(tip.amount, 0)) AS amount
			FROM selected_closings closing
			INNER JOIN `tabPOS Invoice Reference` reference
				ON reference.parent = closing.name
				AND reference.parenttype = 'POS Closing Entry'
				AND reference.parentfield = 'pos_transactions'
			INNER JOIN `tabRestaurant Tip` tip
				ON tip.pos_invoice = reference.pos_invoice
				AND tip.company = closing.company
				AND tip.status = 'Collected'
			INNER JOIN `tabJournal Entry` tip_journal
				ON tip_journal.name = tip.collection_journal_entry
				AND tip_journal.docstatus = 1
			GROUP BY closing.name
		),
		expenses_by_closing AS (
			SELECT
				closing.name AS closing_entry,
				SUM(COALESCE(expense.gto_total, 0)) AS amount
			FROM selected_closings closing
			INNER JOIN `tabResto Gastos` expense
				ON expense.pos_opening_entry = closing.pos_opening_entry
				AND expense.company = closing.company
				AND expense.docstatus = 1
			INNER JOIN `tabJournal Entry` expense_journal
				ON expense_journal.name = expense.journal_entry
				AND expense_journal.docstatus = 1
			GROUP BY closing.name
		),
		closing_summary AS (
			SELECT
				closing.posting_date,
				COALESCE(sales.amount, 0) AS sales_amount,
				COALESCE(tips.amount, 0) AS tip_amount,
				COALESCE(expenses.amount, 0) AS expense_amount
			FROM selected_closings closing
			LEFT JOIN sales_by_closing sales ON sales.closing_entry = closing.name
			LEFT JOIN tips_by_closing tips ON tips.closing_entry = closing.name
			LEFT JOIN expenses_by_closing expenses ON expenses.closing_entry = closing.name
		)
		SELECT
			posting_date AS fecha,
			SUM(sales_amount) AS total_ingreso,
			SUM(tip_amount) AS propinas,
			SUM(expense_amount) AS total_gastos,
			SUM(sales_amount + tip_amount - expense_amount) AS cierre
		FROM closing_summary
		GROUP BY posting_date
		ORDER BY posting_date DESC
		""",
		filters,
		as_dict=True,
	)


def _get_columns():
	return [
		{"fieldname": "fecha", "label": _("Fecha"), "fieldtype": "Date", "width": 110},
		{
			"fieldname": "total_ingreso",
			"label": _("Ventas cobradas"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 160,
		},
		{
			"fieldname": "propinas",
			"label": _("Propinas cobradas"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 160,
		},
		{
			"fieldname": "total_gastos",
			"label": _("Gastos"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{
			"fieldname": "cierre",
			"label": _("Movimiento neto"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 160,
		},
	]
