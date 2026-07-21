# -*- coding: utf-8 -*-
# Copyright (c) 2020, Quantum Bit Core and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from unittest.mock import PropertyMock, patch


from restaurant_management.restaurant_management.doctype.table_order.table_order import (
	get_customer_identity,
	get_voucher_config,
	TableOrder,
)


class TestTableOrder(unittest.TestCase):
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
