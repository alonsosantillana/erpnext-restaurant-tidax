import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.restaurant_management.pos_invoice_merge import (
	reconcile_restaurant_pos_components,
)


def _source(name, grand_total, net_total, tax_total, is_return=0):
	return frappe._dict(
		name=name,
		grand_total=grand_total,
		base_grand_total=grand_total,
		net_total=net_total,
		base_net_total=net_total,
		is_return=is_return,
		taxes=[
			frappe._dict(
				tax_amount_after_discount_amount=tax_total,
				base_tax_amount_after_discount_amount=tax_total,
			)
		],
	)


def _item(source, amount, qty=1):
	return frappe._dict(
		pos_invoice=source,
		amount=amount,
		base_amount=amount,
		rate=amount / qty,
		base_rate=amount / qty,
		net_amount=amount,
		base_net_amount=amount,
		net_rate=amount / qty,
		base_net_rate=amount / qty,
		qty=qty,
		is_free_item=0,
	)


class TestPOSInvoiceMerge(FrappeTestCase):
	def test_cent_residual_is_allocated_to_same_source_item(self):
		invoice = frappe._dict(
			items=[_item("POS-1", 106.88)],
			change_amount=0.01,
			base_change_amount=0.01,
			write_off_amount=-0.01,
			base_write_off_amount=-0.01,
		)
		source = _source("POS-1", 132, 106.88, 25.11)

		reconcile_restaurant_pos_components(invoice, [source], currency_precision=2)

		self.assertEqual(invoice["items"][0].amount, 106.89)
		self.assertEqual(invoice["items"][0].net_amount, 106.89)
		self.assertEqual(invoice.change_amount, 0)
		self.assertEqual(invoice.write_off_amount, 0)
		self.assertEqual(invoice["items"][0].amount + 25.11, source.grand_total)

	def test_each_source_residual_stays_with_its_own_item(self):
		invoice = frappe._dict(
			items=[_item("POS-1", 71.25), _item("POS-2", 97.16)],
		)
		sources = [
			_source("POS-1", 88, 71.25, 16.74),
			_source("POS-2", 120, 97.16, 22.83),
		]

		reconcile_restaurant_pos_components(invoice, sources, currency_precision=2)

		self.assertEqual(invoice["items"][0].amount, 71.26)
		self.assertEqual(invoice["items"][1].amount, 97.17)
		self.assertEqual(sum(item.amount for item in invoice["items"]) + 16.74 + 22.83, 208)

	def test_exact_components_are_not_changed(self):
		invoice = frappe._dict(items=[_item("POS-1", 80)])
		source = _source("POS-1", 98.4, 80, 18.4)

		reconcile_restaurant_pos_components(invoice, [source], currency_precision=2)

		self.assertEqual(invoice["items"][0].amount, 80)

	def test_cent_residual_uses_internal_rate_precision_for_multiple_quantity(self):
		invoice = frappe._dict(items=[_item("POS-1", 70, qty=2)])
		source = _source("POS-1", 86.01, 70, 16)

		reconcile_restaurant_pos_components(invoice, [source], currency_precision=2)

		self.assertEqual(invoice["items"][0].amount, 70.01)
		self.assertEqual(invoice["items"][0].rate, 35.005)

	def test_difference_larger_than_one_cent_is_rejected(self):
		invoice = frappe._dict(items=[_item("POS-1", 79.98)])
		source = _source("POS-1", 98.4, 79.98, 18.4)

		self.assertRaises(
			frappe.ValidationError,
			reconcile_restaurant_pos_components,
			invoice,
			[source],
			2,
		)

	def test_accumulated_three_cent_rounding_is_reconciled_for_many_lines(self):
		amounts = [20.0] * 10 + [2.41]
		invoice = frappe._dict(items=[_item("POS-MANY", amount) for amount in amounts])
		source = frappe._dict(
			name="POS-MANY",
			grand_total=250.0,
			base_grand_total=250.0,
			is_return=0,
			taxes=[
				frappe._dict(
					tax_amount_after_discount_amount=21.25,
					base_tax_amount_after_discount_amount=21.25,
				),
				frappe._dict(
					tax_amount_after_discount_amount=26.31,
					base_tax_amount_after_discount_amount=26.31,
				),
			],
		)

		reconcile_restaurant_pos_components(invoice, [source], currency_precision=2)

		self.assertEqual(invoice["items"][-1].amount, 2.44)
		self.assertAlmostEqual(
			sum(item.amount for item in invoice["items"]) + 21.25 + 26.31,
			250.0,
			places=2,
		)

	def test_many_lines_still_reject_difference_above_rounding_limit(self):
		amounts = [20.0] * 10 + [2.41]
		invoice = frappe._dict(items=[_item("POS-BAD", amount) for amount in amounts])
		source = frappe._dict(
			name="POS-BAD",
			grand_total=250.05,
			base_grand_total=250.05,
			is_return=0,
			taxes=[
				frappe._dict(
					tax_amount_after_discount_amount=21.25,
					base_tax_amount_after_discount_amount=21.25,
				),
				frappe._dict(
					tax_amount_after_discount_amount=26.31,
					base_tax_amount_after_discount_amount=26.31,
				),
			],
		)

		self.assertRaises(
			frappe.ValidationError,
			reconcile_restaurant_pos_components,
			invoice,
			[source],
			2,
		)

	def test_return_rounding_residual_keeps_negative_item_sign(self):
		amounts = [-20.0] * 10 + [-2.41]
		invoice = frappe._dict(items=[_item("POS-RETURN", amount) for amount in amounts])
		source = frappe._dict(
			name="POS-RETURN",
			grand_total=-250.0,
			base_grand_total=-250.0,
			is_return=1,
			taxes=[
				frappe._dict(
					tax_amount_after_discount_amount=-21.25,
					base_tax_amount_after_discount_amount=-21.25,
				),
				frappe._dict(
					tax_amount_after_discount_amount=-26.31,
					base_tax_amount_after_discount_amount=-26.31,
				),
			],
		)

		reconcile_restaurant_pos_components(invoice, [source], currency_precision=2)

		self.assertEqual(invoice["items"][-1].amount, -2.44)
		self.assertLess(invoice["items"][-1].rate, 0)

	def test_document_and_base_residuals_are_reconciled_independently(self):
		amounts = [20.0] * 10 + [2.41]
		items = [_item("POS-FX", amount) for amount in amounts]
		for item in items:
			item.base_amount = item.amount * 2
			item.base_net_amount = item.base_amount
			item.base_rate = item.base_amount / item.qty
			item.base_net_rate = item.base_rate
		invoice = frappe._dict(items=items)
		source = frappe._dict(
			name="POS-FX",
			grand_total=250.0,
			base_grand_total=500.0,
			is_return=0,
			taxes=[
				frappe._dict(
					tax_amount_after_discount_amount=21.25,
					base_tax_amount_after_discount_amount=42.50,
				),
				frappe._dict(
					tax_amount_after_discount_amount=26.31,
					base_tax_amount_after_discount_amount=52.62,
				),
			],
		)

		reconcile_restaurant_pos_components(invoice, [source], currency_precision=2)

		self.assertEqual(invoice["items"][-1].amount, 2.44)
		self.assertEqual(invoice["items"][-1].base_amount, 4.88)
		self.assertAlmostEqual(
			sum(item.base_amount for item in invoice["items"]) + 42.50 + 52.62,
			500.0,
			places=2,
		)

	def test_zero_value_lines_do_not_expand_rounding_tolerance(self):
		items = [_item("POS-ZERO", 79.98)]
		items.extend(_item("POS-ZERO", 0) for _ in range(20))
		invoice = frappe._dict(items=items)
		source = _source("POS-ZERO", 98.4, 79.98, 18.4)

		self.assertRaises(
			frappe.ValidationError,
			reconcile_restaurant_pos_components,
			invoice,
			[source],
			2,
		)
