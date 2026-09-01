# Copyright (c) 2026, Quantum Bit Core and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt


def validate_closing_entry(doc, method=None):
	"""Deduct submitted operational expenses from the expected POS balance."""
	if not doc.get("pos_opening_entry"):
		return

	opening = frappe.db.get_value(
		"POS Opening Entry",
		doc.pos_opening_entry,
		["name", "company"],
		as_dict=True,
	)
	if not opening:
		frappe.throw(_("POS Opening Entry {0} does not exist").format(doc.pos_opening_entry))
	if opening.company != doc.company:
		frappe.throw(_("POS Closing Entry and its expenses must belong to the opening company"))

	opening_amounts = _get_opening_amounts(opening.name)
	sales_amounts = _get_sales_amounts(doc)
	expense_amounts = _get_expense_amounts(opening.name, opening.company, docstatus=1)
	_ensure_reconciliation_rows(
		doc,
		set(opening_amounts) | set(sales_amounts) | set(expense_amounts),
	)
	_apply_reconciliation(
		doc.payment_reconciliation,
		opening_amounts,
		sales_amounts,
		expense_amounts,
	)
	doc.restaurant_expense_total = flt(sum(expense_amounts.values()), 2)


def validate_no_draft_expenses(doc, method=None):
	"""Do not close a shift while an expense could still be omitted."""
	if not doc.get("pos_opening_entry"):
		return

	draft_summary = _get_expense_summary(
		doc.pos_opening_entry,
		doc.company,
		docstatus=0,
	)
	if not draft_summary.count:
		return

	frappe.throw(
		_(
			"There are {0} draft expenses totaling {1}. Submit or delete them before closing the POS."
		).format(
			frappe.bold(draft_summary.count),
			frappe.bold(frappe.format_value(draft_summary.total, {"fieldtype": "Currency"})),
		),
		title=_("Draft expenses pending"),
	)


@frappe.whitelist()
def get_closing_expense_summary(pos_opening_entry):
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.AuthenticationError)

	opening_doc = frappe.get_doc("POS Opening Entry", pos_opening_entry)
	opening_doc.check_permission("read")
	submitted = _get_expense_summary(pos_opening_entry, opening_doc.company, docstatus=1)
	draft = _get_expense_summary(pos_opening_entry, opening_doc.company, docstatus=0)

	return {
		"company": opening_doc.company,
		"total": submitted.total,
		"by_mode_of_payment": submitted.by_mode_of_payment,
		"draft_count": draft.count,
		"draft_total": draft.total,
	}


def _get_opening_amounts(pos_opening_entry):
	rows = frappe.get_all(
		"POS Opening Entry Detail",
		filters={
			"parent": pos_opening_entry,
			"parenttype": "POS Opening Entry",
		},
		fields=["mode_of_payment", "opening_amount"],
	)
	return {row.mode_of_payment: flt(row.opening_amount) for row in rows}


def _get_sales_amounts(doc):
	amounts = defaultdict(float)
	invoice_names = [row.pos_invoice for row in doc.pos_transactions if row.pos_invoice]
	for invoice_name in invoice_names:
		invoice = frappe.get_doc("POS Invoice", invoice_name)
		for payment in invoice.payments:
			amount = flt(payment.amount)
			if payment.account == invoice.account_for_change_amount:
				amount -= flt(invoice.change_amount)
			amounts[payment.mode_of_payment] += amount
	return dict(amounts)


def _get_expense_amounts(pos_opening_entry, company, docstatus=1):
	return _get_expense_summary(
		pos_opening_entry,
		company,
		docstatus=docstatus,
	).by_mode_of_payment


def _get_expense_summary(pos_opening_entry, company, docstatus):
	rows = frappe.db.sql(
		"""
		SELECT
			mode_of_payment,
			COUNT(*) AS expense_count,
			COALESCE(SUM(gto_total), 0) AS amount
		FROM `tabResto Gastos`
		WHERE pos_opening_entry = %(pos_opening_entry)s
		  AND company = %(company)s
		  AND docstatus = %(docstatus)s
		GROUP BY mode_of_payment
		""",
		{
			"pos_opening_entry": pos_opening_entry,
			"company": company,
			"docstatus": docstatus,
		},
		as_dict=True,
	)
	by_mode = {row.mode_of_payment: flt(row.amount) for row in rows}
	return frappe._dict(
		by_mode_of_payment=by_mode,
		count=sum(int(row.expense_count) for row in rows),
		total=flt(sum(by_mode.values()), 2),
	)


def _ensure_reconciliation_rows(doc, modes):
	existing_modes = {row.mode_of_payment for row in doc.payment_reconciliation}
	for mode_of_payment in modes - existing_modes:
		doc.append(
			"payment_reconciliation",
			{
				"mode_of_payment": mode_of_payment,
				"opening_amount": 0,
				"expected_amount": 0,
				"closing_amount": 0,
			},
		)


def _apply_reconciliation(rows, opening_amounts, sales_amounts, expense_amounts):
	for row in rows:
		mode_of_payment = row.mode_of_payment
		opening_amount = flt(opening_amounts.get(mode_of_payment))
		sales_amount = flt(sales_amounts.get(mode_of_payment))
		expense_amount = flt(expense_amounts.get(mode_of_payment))
		gross_expected = opening_amount + sales_amount
		net_expected = gross_expected - expense_amount
		previous_expected = flt(row.get("expected_amount"))
		closing_amount = flt(row.get("closing_amount"))

		row.opening_amount = opening_amount
		row.restaurant_sales_amount = sales_amount
		row.restaurant_expense_amount = expense_amount
		row.expected_amount = net_expected
		if abs(closing_amount - previous_expected) < 0.005:
			row.closing_amount = net_expected
		row.difference = flt(row.closing_amount) - net_expected
