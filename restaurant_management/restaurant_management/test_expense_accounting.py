from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.restaurant_management.expense_accounting import (
	cancel_expense_journal_entry,
	create_expense_journal_entry,
	validate_expense_accounting_before_closing,
	validate_expense_accounts,
)


MODULE = "restaurant_management.restaurant_management.expense_accounting"


class TestExpenseAccounting(FrappeTestCase):
	@patch(f"{MODULE}._validate_cost_center")
	@patch(f"{MODULE}._validate_account_currency")
	@patch(f"{MODULE}._validate_account")
	@patch(f"{MODULE}._get_item_expense_account")
	@patch(f"{MODULE}._get_accounting_settings")
	def test_item_expense_account_has_priority_over_company_fallback(
		self, get_settings, get_item_account, validate_account, validate_currency, validate_cost_center
	):
		get_settings.return_value = frappe._dict(
			default_expense_account="General Expense - A",
			expense_cost_center="Main - A",
		)
		get_item_account.return_value = "Taxi Expense - A"
		row = frappe._dict(idx=1, item_gto="GTO-001", expense_account=None)
		doc = frappe._dict(
			company="Company A",
			payment_account="Cash - A",
			gto_detalle=[row],
		)

		validate_expense_accounts(doc)

		self.assertEqual(row.expense_account, "Taxi Expense - A")
		validate_account.assert_any_call("Taxi Expense - A", "Company A", "Expense")
		validate_account.assert_any_call("Cash - A", "Company A", "Asset")
		validate_currency.assert_called_once_with("Cash - A", "Company A")
		validate_cost_center.assert_called_once_with("Main - A", "Company A")

	@patch(f"{MODULE}._validate_cost_center")
	@patch(f"{MODULE}._validate_account_currency")
	@patch(f"{MODULE}._validate_account")
	@patch(f"{MODULE}._get_item_expense_account", return_value=None)
	@patch(f"{MODULE}._get_accounting_settings")
	def test_company_fallback_is_used_when_item_has_no_expense_account(
		self, get_settings, get_item_account, validate_account, validate_currency, validate_cost_center
	):
		get_settings.return_value = frappe._dict(
			default_expense_account="General Expense - A",
			expense_cost_center="Main - A",
		)
		row = frappe._dict(idx=1, item_gto="GTO-001", expense_account=None)
		doc = frappe._dict(
			company="Company A",
			payment_account="Cash - A",
			gto_detalle=[row],
		)

		validate_expense_accounts(doc)

		self.assertEqual(row.expense_account, "General Expense - A")

	@patch(f"{MODULE}._get_accounting_settings")
	@patch(f"{MODULE}.validate_expense_accounts")
	@patch(f"{MODULE}._validate_account_currency")
	@patch(f"{MODULE}.frappe.new_doc")
	@patch(f"{MODULE}.frappe.db.get_value")
	def test_submit_creates_balanced_journal_entry(
		self, get_value, new_doc, validate_currency, validate_accounts, get_settings
	):
		get_value.return_value = None
		get_settings.return_value = frappe._dict(expense_cost_center="Main - A")
		journal = MagicMock()
		journal.name = "JV-TEST-1"
		journal_rows = []
		journal.append.side_effect = lambda table, values: journal_rows.append(values)
		new_doc.return_value = journal
		doc = MagicMock(
			journal_entry=None,
			company="Company A",
			date_gto="2026-09-01",
			name="GTO-A-1",
			pos_opening_entry="OPEN-A-1",
			payment_account="Cash - A",
			gto_total=30,
			gto_detalle=[
				frappe._dict(expense_account="Taxi - A", importe_gto=10),
				frappe._dict(expense_account="Meals - A", importe_gto=20),
			],
		)

		create_expense_journal_entry(doc)

		self.assertEqual(sum(row.get("debit_in_account_currency", 0) for row in journal_rows), 30)
		self.assertEqual(sum(row.get("credit_in_account_currency", 0) for row in journal_rows), 30)
		self.assertEqual(journal_rows[-1]["account"], "Cash - A")
		journal.insert.assert_called_once()
		journal.submit.assert_called_once()
		doc.db_set.assert_called_once_with("journal_entry", "JV-TEST-1", update_modified=False)

	@patch(f"{MODULE}.frappe.get_doc")
	def test_cancel_expense_cancels_submitted_journal(self, get_doc):
		journal = MagicMock(docstatus=1)
		get_doc.return_value = journal
		doc = frappe._dict(journal_entry="JV-TEST-1")

		cancel_expense_journal_entry(doc)

		journal.cancel.assert_called_once()

	@patch(f"{MODULE}.get_unposted_submitted_expenses")
	def test_closing_is_blocked_when_submitted_expense_has_no_valid_journal(self, get_unposted):
		get_unposted.return_value = ["GTO-A-1"]
		doc = frappe._dict(pos_opening_entry="OPEN-A-1", company="Company A")

		self.assertRaises(
			frappe.ValidationError,
			validate_expense_accounting_before_closing,
			doc,
		)
