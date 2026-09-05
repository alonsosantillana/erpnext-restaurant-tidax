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

		with (
			patch.object(restaurant_tip, "_get_locked_tip", return_value=tip),
			patch.object(restaurant_tip, "_require_tip_management_permission"),
			patch.object(restaurant_tip, "_cancel_tip_document"),
			patch.object(frappe, "get_doc", return_value=replacement),
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


if __name__ == "__main__":
	unittest.main()
