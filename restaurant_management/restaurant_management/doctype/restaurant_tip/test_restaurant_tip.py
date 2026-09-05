import unittest
from unittest.mock import MagicMock, patch

import frappe

from restaurant_management.restaurant_management.doctype.restaurant_tip import restaurant_tip


class TestRestaurantTip(unittest.TestCase):
	def test_cancellation_reason_is_required_and_bounded(self):
		with self.assertRaises(frappe.ValidationError):
			restaurant_tip._validate_cancellation_reason(" no ")

		reason = restaurant_tip._validate_cancellation_reason("x" * 600)
		self.assertEqual(len(reason), 500)

	def test_cashier_cannot_manage_closed_shift_tip(self):
		tip = frappe._dict(company="ERP CLOUD", pos_invoice="POS-INV-1")
		with (
			patch.object(frappe, "get_roles", return_value=["resto_cajero"]),
			patch.object(frappe, "has_permission", return_value=True),
			patch.object(
				restaurant_tip,
				"_get_tip_cash_session",
				return_value=frappe._dict(opening_entry="OPEN-1", closing_entry="CLOSE-1"),
			),
			self.assertRaises(frappe.PermissionError),
		):
			restaurant_tip._require_tip_management_permission(tip)

	def test_admin_can_manage_closed_shift_tip(self):
		tip = frappe._dict(company="ERP CLOUD", pos_invoice="POS-INV-1")
		with (
			patch.object(frappe, "get_roles", return_value=["resto_admin"]),
			patch.object(frappe, "has_permission", return_value=True),
			patch.object(
				restaurant_tip,
				"_get_tip_cash_session",
				return_value=frappe._dict(opening_entry="OPEN-1", closing_entry="CLOSE-1"),
			),
		):
			result = restaurant_tip._require_tip_management_permission(tip)

		self.assertEqual(result.closing_entry, "CLOSE-1")

	def test_waiter_cannot_manage_tip(self):
		tip = frappe._dict(company="ERP CLOUD", pos_invoice="POS-INV-1")
		with (
			patch.object(frappe, "get_roles", return_value=["resto_mozo"]),
			self.assertRaises(frappe.PermissionError),
		):
			restaurant_tip._require_tip_management_permission(tip)

	def test_rectification_rolls_back_when_replacement_posting_fails(self):
		tip = frappe._dict(
			name="TIP-1",
			company="ERP CLOUD",
			posting_date="2026-09-05",
			posting_time="12:00:00",
			table_order="ORDER-1",
			pos_invoice="POS-INV-1",
			pos_profile="Resto",
			amount=5,
			mode_of_payment="Cash",
			collection_account="Cash - EC",
			liability_account="Tips - EC",
			waiter="waiter@example.com",
		)
		replacement = MagicMock(status="Pending Accounting")
		replacement.insert.return_value = replacement
		original_get_doc = frappe.get_doc

		with (
			patch.object(restaurant_tip, "_get_locked_tip", return_value=tip),
			patch.object(restaurant_tip, "_require_tip_management_permission"),
			patch.object(restaurant_tip, "_cancel_tip_document"),
			patch.object(
				frappe,
				"get_doc",
				side_effect=lambda *args, **kwargs: replacement
				if len(args) == 1 and isinstance(args[0], dict)
				else original_get_doc(*args, **kwargs),
			),
			patch.object(restaurant_tip, "post_tip_collection", side_effect=RuntimeError("posting failed")),
			patch.object(frappe.db, "savepoint"),
			patch.object(frappe.db, "rollback") as rollback,
			self.assertRaises(RuntimeError),
		):
			restaurant_tip.rectify_restaurant_tip("TIP-1", 7, "amount correction", 1)

		rollback.assert_called_once_with(save_point="rectify_restaurant_tip")

	def test_invoice_cancellation_reverses_all_active_tip_versions(self):
		doc = frappe._dict(name="POS-INV-1")
		tips = {
			"TIP-1": frappe._dict(name="TIP-1"),
			"TIP-2": frappe._dict(name="TIP-2"),
		}

		with (
			patch.object(frappe, "get_all", return_value=list(tips)) as get_all,
			patch.object(frappe, "get_doc", side_effect=lambda doctype, name: tips[name]),
			patch.object(restaurant_tip, "_cancel_tip_document") as cancel_tip,
		):
			restaurant_tip.cancel_tip_for_invoice(doc)

		get_all.assert_called_once_with(
			"Restaurant Tip",
			filters={"pos_invoice": "POS-INV-1", "status": ["!=", "Cancelled"]},
			pluck="name",
		)
		self.assertEqual(cancel_tip.call_count, 2)



	def test_settlement_requires_one_waiter(self):
		tips = [
			frappe._dict(name="TIP-1", status="Collected", company="ERP CLOUD", waiter="one@example.com", liability_account="Tips - EC", amount=5, collection_journal_entry="JV-COLLECT-1"),
			frappe._dict(name="TIP-2", status="Collected", company="ERP CLOUD", waiter="two@example.com", liability_account="Tips - EC", amount=7, collection_journal_entry="JV-COLLECT-2"),
		]
		session = frappe._dict(closing_entry="CLOSE-1", closing_time="2026-09-05 12:00:00", cashier="cashier@example.com")
		with (
			patch.object(frappe.db, "get_value", return_value=1),
			patch.object(restaurant_tip, "_get_tip_cash_session", return_value=session),
			self.assertRaises(frappe.ValidationError),
		):
			restaurant_tip._validate_tip_settlement(tips, "2026-09-05")

	def test_settlement_rejects_waiter_role(self):
		tip = frappe._dict(name="TIP-1", status="Collected", company="ERP CLOUD", waiter="waiter@example.com", liability_account="Tips - EC", amount=5, collection_journal_entry="JV-COLLECT-1")
		session = frappe._dict(closing_entry="CLOSE-1", closing_time="2026-09-05 12:00:00", cashier="cashier@example.com")
		with (
			patch.object(frappe.db, "get_value", return_value=1),
			patch.object(restaurant_tip, "_get_tip_cash_session", return_value=session),
			patch.object(frappe, "get_roles", return_value=["resto_mozo"]),
			self.assertRaises(frappe.PermissionError),
		):
			restaurant_tip._validate_tip_settlement([tip], "2026-09-05")

	def test_settlement_posts_one_balanced_journal_entry(self):
		tips = [
			frappe._dict(name="TIP-1", amount=5, collection_journal_entry="JV-COLLECT-1", pos_invoice="POS-1"),
			frappe._dict(name="TIP-2", amount=7, collection_journal_entry="JV-COLLECT-2", pos_invoice="POS-2"),
		]
		context = frappe._dict(company="ERP CLOUD", waiter="waiter@example.com", liability_account="Tips - EC", closing_entry="CLOSE-1", total=12)
		journal = MagicMock(name="journal")
		journal.name = "JV-PAYOUT-1"

		with (
			patch.object(restaurant_tip, "_get_locked_tips", return_value=tips),
			patch.object(restaurant_tip, "_validate_tip_settlement", return_value=context),
			patch.object(restaurant_tip, "_get_mode_of_payment_account", return_value="Cash - EC"),
			patch.object(frappe, "new_doc", return_value=journal),
			patch.object(frappe.db, "savepoint"),
			patch.object(frappe.db, "set_value") as set_value,
		):
			result = restaurant_tip.settle_restaurant_tips(["TIP-1", "TIP-2"], "Cash", "2026-09-05")

		self.assertEqual(journal.append.call_count, 3)
		self.assertEqual(journal.append.call_args_list[0].args[1]["debit_in_account_currency"], 5)
		self.assertEqual(journal.append.call_args_list[0].args[1]["reference_name"], "JV-COLLECT-1")
		self.assertEqual(journal.append.call_args_list[1].args[1]["debit_in_account_currency"], 7)
		self.assertEqual(journal.append.call_args_list[1].args[1]["reference_name"], "JV-COLLECT-2")
		self.assertEqual(journal.append.call_args_list[2].args[1]["credit_in_account_currency"], 12)
		journal.insert.assert_called_once_with()
		journal.submit.assert_called_once_with()
		self.assertEqual(set_value.call_count, 2)
		self.assertEqual(result["journal_entry"], "JV-PAYOUT-1")

	def test_cancelled_settlement_restores_tips_to_collected(self):
		doc = frappe._dict(name="JV-PAYOUT-1")
		with (
			patch.object(frappe, "get_all", return_value=["TIP-1", "TIP-2"]),
			patch.object(frappe.db, "set_value") as set_value,
		):
			restaurant_tip.restore_tips_for_cancelled_settlement(doc)

		self.assertEqual(set_value.call_count, 2)
		for call in set_value.call_args_list:
			self.assertEqual(call.args[2]["status"], "Collected")
			self.assertIsNone(call.args[2]["settlement_journal_entry"])


if __name__ == "__main__":
	unittest.main()
