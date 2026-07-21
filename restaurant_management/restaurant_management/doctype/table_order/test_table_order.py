# -*- coding: utf-8 -*-
# Copyright (c) 2020, Quantum Bit Core and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch


from restaurant_management.restaurant_management.doctype.table_order.table_order import (
	apply_pos_tax_inclusion,
	get_customer_identity,
	get_voucher_config,
	TableOrder,
)
from restaurant_management.api import DOCUMENT_METHODS, READ_ONLY_DOCUMENT_METHODS


class TestTableOrder(unittest.TestCase):
	def test_pos_profile_tax_inclusion_overrides_loaded_tax_rows(self):
		invoice = frappe._dict(taxes=[
			frappe._dict(included_in_print_rate=0),
			frappe._dict(included_in_print_rate=0),
		])

		apply_pos_tax_inclusion(invoice, 1)

		self.assertEqual(
			[tax.included_in_print_rate for tax in invoice.taxes],
			[1, 1],
		)

	@patch(
		"restaurant_management.restaurant_management.restaurant_manage.check_exceptions"
	)
	def test_push_item_returns_server_calculated_payload(self, check_exceptions):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "OR-2026-00001",
			"customer": "CUSTOMER-1",
		})
		event = {"action": "Update", "data": {"items": [{"tax_amount": 5.76}]}}

		with patch.object(TableOrder, "update_item", return_value="aggregate"), patch.object(
			TableOrder, "aggregate"
		), patch.object(TableOrder, "synchronize", return_value=event) as synchronize:
			result = order.push_item({"identifier": "ITEM-1"})

		self.assertEqual(result, event)
		synchronize.assert_called_once_with({"item": "ITEM-1"})

	def test_items_list_includes_server_calculated_tax_amount(self):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "OR-2026-00001",
			"table": "TABLE-1",
			"entry_items": [{
				"doctype": "Order Entry Item",
				"identifier": "ITEM-1",
				"item_code": "PLT-001",
				"item_name": "Ceviche",
				"qty": 1,
				"rate": 32,
				"tax_amount": 5.76,
				"amount": 37.76,
			}],
		})
		table = MagicMock()
		table.order_short_name.return_value = "00001"
		table.process_status_data.return_value = {}

		with patch.object(TableOrder, "_table", new_callable=PropertyMock) as table_property:
			table_property.return_value = table
			items = order.items_list()

		self.assertEqual(items[0]["tax_amount"], 5.76)

	def test_runtime_assets_do_not_reference_legacy_dinners_name(self):
		assets_path = Path(
			frappe.get_app_path("restaurant_management", "public", "restaurant", "js")
		)
		legacy_references = [
			str(path.relative_to(assets_path))
			for path in assets_path.glob("*.js")
			if "dinners" in path.read_text(encoding="utf-8").lower()
		]

		self.assertEqual(legacy_references, [])

	def test_short_data_exposes_guest_count(self):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "OR-2026-00001",
			"table": "TABLE-1",
			"customer": "CUSTOMER-1",
			"status": "Attending",
			"guest_count": 4,
			"tax": 0,
			"amount": 100,
		})

		with patch.object(
			TableOrder, "items_count", new_callable=PropertyMock, return_value=0
		), patch.object(
			TableOrder, "products_not_ordered_count", new_callable=PropertyMock, return_value=0
		):
			data = order.short_data()["data"]

		self.assertEqual(data["guest_count"], 4)
		self.assertNotIn("dinners", data)

	def test_short_data_exposes_global_discount(self):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "OR-2026-00001",
			"table": "TABLE-1",
			"customer": "CUSTOMER-1",
			"status": "Attending",
			"discount": 12,
			"discount_global_percent": 0,
			"tax": 18,
			"amount": 118,
		})

		with patch.object(
			TableOrder, "items_count", new_callable=PropertyMock, return_value=1
		), patch.object(
			TableOrder, "products_not_ordered_count", new_callable=PropertyMock, return_value=0
		):
			data = order.short_data()["data"]

		self.assertEqual(data["discount"], 12)
		self.assertEqual(data["discount_global_percent"], 0)

	@patch.object(frappe.db, "get_value", return_value=1)
	def test_global_discount_accepts_one_supported_mode(self, get_value):
		for values in (
			{"discount": 20, "discount_global_percent": 0},
			{"discount": 0, "discount_global_percent": 15},
		):
			with self.subTest(values=values):
				order = TableOrder({
					"doctype": "Table Order",
					"pos_profile": "RESTO",
					"amount": 100,
					**values,
				})
				order.validate_global_discount()

	@patch.object(frappe.db, "get_value", return_value=1)
	def test_global_discount_rejects_invalid_values(self, get_value):
		invalid_values = (
			{"discount": -1, "discount_global_percent": 0},
			{"discount": 0, "discount_global_percent": -1},
			{"discount": 0, "discount_global_percent": 101},
			{"discount": 10, "discount_global_percent": 10},
			{"discount": 101, "discount_global_percent": 0},
		)
		for values in invalid_values:
			with self.subTest(values=values):
				order = TableOrder({
					"doctype": "Table Order",
					"pos_profile": "RESTO",
					"amount": 100,
					**values,
				})
				with self.assertRaises(frappe.ValidationError):
					order.validate_global_discount()

	@patch.object(frappe.db, "get_value", return_value=0)
	def test_global_discount_respects_pos_profile_permission(self, get_value):
		order = TableOrder({
			"doctype": "Table Order",
			"pos_profile": "RESTO",
			"amount": 100,
			"discount": 10,
		})

		with self.assertRaises(frappe.ValidationError):
			order.validate_global_discount()

	def test_recalculating_items_preserves_fixed_global_discount(self):
		order = TableOrder({
			"doctype": "Table Order",
			"discount": 10,
			"amount": 100,
		})
		invoice = MagicMock(
			items=[],
			base_total_taxes_and_charges=18,
			grand_total=118,
		)

		with patch.object(order, "get_invoice", return_value=invoice), patch.object(
			order, "save"
		):
			order.calculate_order([])

		self.assertEqual(order.discount, 10)
		self.assertEqual(order.amount, 118)

	def test_aggregate_uses_full_invoice_totals(self):
		order = TableOrder({
			"doctype": "Table Order",
			"entry_items": [{
				"doctype": "Order Entry Item",
				"identifier": "ITEM-1",
				"qty": 1,
			}],
		})
		invoice = MagicMock(
			base_total_taxes_and_charges=22.96,
			grand_total=150.50,
		)

		with patch.object(order, "get_invoice", return_value=invoice) as get_invoice, patch.object(
			order, "save"
		):
			order.aggregate()

		self.assertEqual(order.tax, 22.96)
		self.assertEqual(order.amount, 150.50)
		self.assertIn("ITEM-1", get_invoice.call_args.args[0])

	@patch(
		"restaurant_management.restaurant_management.doctype.table_order.table_order.frappe.render_template"
	)
	@patch.object(TableOrder, "items_list")
	def test_divide_template_uses_the_same_tax_inclusive_totals_as_the_modal(
		self, items_list, render_template
	):
		items_list.return_value = [
			{"qty": 2, "rate": 32, "amount": 75.52},
			{"qty": 1, "rate": 10, "amount": 11.80},
		]
		render_template.return_value = "divide-template"
		order = TableOrder({"doctype": "Table Order", "name": "ORDER-1", "table": "TABLE-1"})

		self.assertEqual(order.divide_template(), "divide-template")
		context = render_template.call_args.args[1]
		self.assertEqual(context["divide_total"], 74)
		self.assertEqual(
			[item["divide_amount"] for item in context["items"]],
			[64, 10],
		)

	def test_divide_template_is_an_allowed_read_only_operation(self):
		self.assertIn("divide_template", DOCUMENT_METHODS["Table Order"])
		self.assertIn(("Table Order", "divide_template"), READ_ONLY_DOCUMENT_METHODS)

	def test_divide_quantities_are_validated_before_mutation(self):
		order = TableOrder({
			"doctype": "Table Order",
			"entry_items": [
				{
					"doctype": "Order Entry Item",
					"identifier": "ITEM-1",
					"item_code": "DISH-1",
					"item_name": "Dish 1",
					"status": "Completed",
					"qty": 2,
				},
				{
					"doctype": "Order Entry Item",
					"identifier": "ITEM-2",
					"item_code": "DISH-2",
					"item_name": "Dish 2",
					"status": "Completed",
					"qty": 1,
				},
			],
		})

		self.assertEqual(
			order.validate_divide_items({"ITEM-1": {"qty": 1}}),
			{"ITEM-1": 1},
		)
		with self.assertRaises(frappe.ValidationError):
			order.validate_divide_items({"ITEM-1": {"qty": 3}})
		with self.assertRaises(frappe.ValidationError):
			order.validate_divide_items({
				"ITEM-1": {"qty": 2},
				"ITEM-2": {"qty": 1},
			})

	@patch(
		"restaurant_management.restaurant_management.doctype.table_order.table_order.frappe.publish_realtime"
	)
	def test_synchronize_returns_the_published_event(self, publish_realtime):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "ORDER-TEST",
			"table": "TABLE-TEST",
		})
		expected_data = {"order": {"data": {"name": "ORDER-TEST"}}, "items": []}

		with patch.object(TableOrder, "data", return_value=expected_data), patch.object(
			TableOrder, "_table", new_callable=PropertyMock
		) as table:
			event = order.synchronize({
				"action": "Transfer",
				"client": "client-test",
				"last_table": "TABLE-OLD",
			})

		self.assertEqual(event, {
			"action": "Transfer",
			"data": expected_data,
			"client": "client-test",
			"item_removed": None,
		})
		publish_realtime.assert_called_once_with(
			"synchronize_order_data", event, after_commit=True
		)
		table.return_value.synchronize.assert_called_once_with()

	def test_voucher_series_matrix(self):
		cases = {
			("Boleta", "Electrónica"): ("serie_boleta", "03", "1"),
			("Boleta", "Manual"): ("serie_boleta_m", "03", "1"),
			("Factura", "Electrónica"): ("serie_factura", "01", "6"),
			("Factura", "Manual"): ("serie_factura_m", "01", "6"),
		}

		for choices, expected in cases.items():
			with self.subTest(choices=choices):
				config = get_voucher_config(*choices)
				self.assertEqual(
					(config["series_field"], config["document_code"], config["identity_code"]),
					expected,
				)

	def test_voucher_choices_are_required(self):
		with self.assertRaises(frappe.ValidationError):
			get_voucher_config(None, None)

	def test_unknown_voucher_combination_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			get_voucher_config("Ticket", "Electrónica")

	def test_customer_identity_matches_voucher(self):
		cases = {
			"Boleta": frappe._dict(
				tax_id="12345678",
				tipo_documento_identidad="DOCUMENTO NACIONAL DE IDENTIDAD (DNI)",
				codigo_tipo_documento="1",
			),
			"Factura": frappe._dict(
				tax_id="20123456789",
				tipo_documento_identidad="REGISTRO ÚNICO DE CONTRIBUYENTES",
				codigo_tipo_documento="6",
			),
		}

		for voucher_type, identity in cases.items():
			with self.subTest(voucher_type=voucher_type):
				config = get_voucher_config(voucher_type, "Electrónica")
				with patch.object(frappe.db, "get_value", return_value=identity):
					self.assertEqual(get_customer_identity("TEST", config), identity)

	def test_customer_identity_mismatch_is_rejected(self):
		config = get_voucher_config("Factura", "Electrónica")
		dni = frappe._dict(
			tax_id="12345678",
			tipo_documento_identidad="DOCUMENTO NACIONAL DE IDENTIDAD (DNI)",
			codigo_tipo_documento="1",
		)
		with patch.object(frappe.db, "get_value", return_value=dni):
			with self.assertRaises(frappe.ValidationError):
				get_customer_identity("TEST", config)
