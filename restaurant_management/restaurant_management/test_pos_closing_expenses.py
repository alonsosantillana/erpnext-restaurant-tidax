from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.restaurant_management.pos_closing_expenses import (
	_apply_reconciliation,
	validate_no_draft_expenses,
)


class TestPOSClosingExpenses(FrappeTestCase):
	def test_expenses_reduce_expected_amount_by_payment_method(self):
		rows = [
			frappe._dict(
				mode_of_payment="Efectivo",
				opening_amount=100,
				expected_amount=600,
				closing_amount=600,
			)
		]
		_apply_reconciliation(
			rows,
			{"Efectivo": 100},
			{"Efectivo": 500},
			{"Efectivo": 80},
		)

		self.assertEqual(rows[0].restaurant_sales_amount, 500)
		self.assertEqual(rows[0].restaurant_expense_amount, 80)
		self.assertEqual(rows[0].expected_amount, 520)
		self.assertEqual(rows[0].closing_amount, 520)
		self.assertEqual(rows[0].difference, 0)

	def test_reconciliation_is_idempotent(self):
		rows = [
			frappe._dict(
				mode_of_payment="Efectivo",
				opening_amount=100,
				expected_amount=600,
				closing_amount=600,
			)
		]
		for _ in range(2):
			_apply_reconciliation(
				rows,
				{"Efectivo": 100},
				{"Efectivo": 500},
				{"Efectivo": 80},
			)

		self.assertEqual(rows[0].expected_amount, 520)
		self.assertEqual(rows[0].closing_amount, 520)
		self.assertEqual(rows[0].difference, 0)

	def test_manual_closing_amount_is_preserved(self):
		rows = [
			frappe._dict(
				mode_of_payment="Efectivo",
				opening_amount=100,
				expected_amount=600,
				closing_amount=515,
			)
		]
		_apply_reconciliation(
			rows,
			{"Efectivo": 100},
			{"Efectivo": 500},
			{"Efectivo": 80},
		)

		self.assertEqual(rows[0].expected_amount, 520)
		self.assertEqual(rows[0].closing_amount, 515)
		self.assertEqual(rows[0].difference, -5)

	@patch(
		"restaurant_management.restaurant_management.pos_closing_expenses._get_expense_summary"
	)
	def test_draft_expenses_block_submission(self, get_expense_summary):
		get_expense_summary.return_value = frappe._dict(count=2, total=35)
		doc = MagicMock(pos_opening_entry="POS-OPE-1", company="Company A")
		doc.get.side_effect = lambda fieldname: getattr(doc, fieldname, None)

		self.assertRaises(
			frappe.ValidationError,
			validate_no_draft_expenses,
			doc,
		)
