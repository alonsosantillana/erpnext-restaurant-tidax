# Copyright (c) 2026, Quantum Bit Core and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt


def validate_expense_accounts(doc, method=None):
	"""Resolve and validate the debit account for every restaurant expense row."""
	if not doc.company or not doc.get("gto_detalle"):
		return

	settings = _get_accounting_settings(doc.company)
	for row in doc.gto_detalle:
		expense_account = resolve_expense_account(row.item_gto, doc.company)
		if not expense_account:
			frappe.throw(
				_(
					"Row {0}: configure an Expense Account for Item {1} in Item Default "
					"or set the Default Restaurant Expense Account for company {2}"
				).format(row.idx, row.item_gto, doc.company),
				title=_("Expense account required"),
			)
		row.expense_account = expense_account

	_validate_account(doc.payment_account, doc.company, "Asset")
	_validate_account_currency(doc.payment_account, doc.company)
	_validate_cost_center(settings.expense_cost_center, doc.company)


def create_expense_journal_entry(doc, method=None):
	"""Post the operational expense when Resto Gastos is submitted."""
	if doc.journal_entry:
		journal_status = frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus")
		if journal_status == 1:
			return
		frappe.throw(
			_("Linked Journal Entry {0} is not submitted").format(doc.journal_entry),
			title=_("Invalid expense accounting"),
		)

	validate_expense_accounts(doc)
	settings = _get_accounting_settings(doc.company)
	grouped_expenses = defaultdict(float)
	for row in doc.gto_detalle:
		grouped_expenses[row.expense_account] += flt(row.importe_gto)

	journal_entry = frappe.new_doc("Journal Entry")
	journal_entry.company = doc.company
	journal_entry.posting_date = doc.date_gto
	journal_entry.voucher_type = "Journal Entry"
	journal_entry.user_remark = _("Restaurant expense {0} for POS opening {1}").format(
		doc.name, doc.pos_opening_entry
	)
	debit_total = 0
	for expense_account, amount in sorted(grouped_expenses.items()):
		_validate_account_currency(expense_account, doc.company)
		amount = flt(amount, 2)
		debit_total += amount
		journal_entry.append(
			"accounts",
			{
				"account": expense_account,
				"debit_in_account_currency": amount,
				"credit_in_account_currency": 0,
				"cost_center": settings.expense_cost_center,
			},
		)
	if abs(debit_total - flt(doc.gto_total, 2)) > 0.005:
		frappe.throw(_("Expense detail total does not match the document total"))

	journal_entry.append(
		"accounts",
		{
			"account": doc.payment_account,
			"debit_in_account_currency": 0,
			"credit_in_account_currency": debit_total,
		},
	)
	journal_entry.flags.ignore_permissions = True
	journal_entry.insert()
	journal_entry.submit()

	doc.db_set("journal_entry", journal_entry.name, update_modified=False)
	doc.journal_entry = journal_entry.name


def cancel_expense_journal_entry(doc, method=None):
	if not doc.journal_entry:
		return

	journal_entry = frappe.get_doc("Journal Entry", doc.journal_entry)
	if journal_entry.docstatus == 1:
		journal_entry.flags.ignore_permissions = True
		journal_entry.cancel()


def validate_company_settings_expense_accounting(doc, method=None):
	if doc.default_expense_account:
		_validate_account(doc.default_expense_account, doc.company, "Expense")
		_validate_account_currency(doc.default_expense_account, doc.company)
	if doc.expense_cost_center:
		_validate_cost_center(doc.expense_cost_center, doc.company)


def get_unposted_submitted_expenses(pos_opening_entry, company):
	rows = frappe.db.sql(
		"""
		SELECT expense.name
		FROM `tabResto Gastos` expense
		LEFT JOIN `tabJournal Entry` journal
		  ON journal.name = expense.journal_entry
		WHERE expense.pos_opening_entry = %(pos_opening_entry)s
		  AND expense.company = %(company)s
		  AND expense.docstatus = 1
		  AND (COALESCE(expense.journal_entry, '') = '' OR COALESCE(journal.docstatus, -1) != 1)
		ORDER BY expense.name
		""",
		{"pos_opening_entry": pos_opening_entry, "company": company},
		as_list=True,
	)
	return [row[0] for row in rows]


def validate_expense_accounting_before_closing(doc, method=None):
	if not doc.get("pos_opening_entry"):
		return
	unposted = get_unposted_submitted_expenses(doc.pos_opening_entry, doc.company)
	if unposted:
		frappe.throw(
			_("Submitted restaurant expenses without a valid accounting entry: {0}").format(
				", ".join(unposted)
			),
			title=_("Expense accounting pending"),
		)


def resolve_expense_account(item_code, company):
	"""Return the validated item-specific or company fallback expense account."""
	settings = _get_accounting_settings(company)
	expense_account = _get_item_expense_account(item_code, company)
	expense_account = expense_account or settings.default_expense_account
	if expense_account:
		_validate_account(expense_account, company, "Expense")
	return expense_account


def _get_accounting_settings(company):
	settings = frappe.db.get_value(
		"Restaurant Company Settings",
		company,
		["default_expense_account", "expense_cost_center"],
		as_dict=True,
	) or frappe._dict()
	if not settings.expense_cost_center:
		settings.expense_cost_center = frappe.db.get_value("Company", company, "cost_center")
	return settings


def _get_item_expense_account(item_code, company):
	if not item_code:
		return None
	return frappe.db.get_value(
		"Item Default",
		{"parent": item_code, "parenttype": "Item", "company": company},
		"expense_account",
	)


def _validate_account(account_name, company, root_type):
	if not account_name:
		frappe.throw(_("Accounting account is required"))
	account = frappe.db.get_value(
		"Account",
		account_name,
		["company", "root_type", "is_group", "disabled"],
		as_dict=True,
	)
	if not account or account.disabled:
		frappe.throw(_("Account {0} must be enabled").format(account_name))
	if account.company != company:
		frappe.throw(_("Account {0} must belong to company {1}").format(account_name, company))
	if account.is_group or account.root_type != root_type:
		frappe.throw(
			_("Account {0} must be a non-group {1} account").format(account_name, root_type)
		)


def _validate_account_currency(account_name, company):
	account_currency = frappe.db.get_value("Account", account_name, "account_currency")
	company_currency = frappe.db.get_value("Company", company, "default_currency")
	if account_currency and company_currency and account_currency != company_currency:
		frappe.throw(
			_(
				"Restaurant expense accounting currently requires account {0} to use company currency {1}"
			).format(account_name, company_currency)
		)


def _validate_cost_center(cost_center, company):
	if not cost_center:
		frappe.throw(
			_("Configure a Restaurant Expense Cost Center or a default Company cost center for {0}").format(company)
		)
	value = frappe.db.get_value(
		"Cost Center", cost_center, ["company", "is_group", "disabled"], as_dict=True
	)
	if not value or value.disabled or value.is_group or value.company != company:
		frappe.throw(
			_("Expense Cost Center must be an enabled non-group Cost Center for company {0}").format(company)
		)
