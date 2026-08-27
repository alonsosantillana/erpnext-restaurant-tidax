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
from restaurant_management.api import (
	DOCUMENT_METHODS,
	READ_ONLY_DOCUMENT_METHODS,
	_get_account_print_configuration,
	call as call_restaurant_api,
	print_order_account,
)


class TestTableOrder(unittest.TestCase):
	@patch("restaurant_management.api._require_authenticated_user")
	@patch("restaurant_management.api.frappe.has_permission", return_value=True)
	@patch("restaurant_management.api.frappe.get_doc")
	def test_add_order_uses_table_read_and_order_create_permissions(
		self, get_doc, has_permission, require_authenticated_user
	):
		table = MagicMock()
		table.add_order.return_value = {"name": "OR-2026-00008"}
		get_doc.return_value = table

		result = call_restaurant_api(
			"Restaurant Object",
			"T2",
			"add_order",
			{"client": "Consumidor Final"},
		)

		table.check_permission.assert_called_once_with("read")
		has_permission.assert_called_once_with("Table Order", "create")
		table.add_order.assert_called_once_with(client="Consumidor Final")
		self.assertEqual(result, {"name": "OR-2026-00008"})

	@patch("restaurant_management.api._require_authenticated_user")
	@patch("restaurant_management.api.frappe.has_permission", return_value=False)
	@patch("restaurant_management.api.frappe.get_doc")
	def test_add_order_is_denied_without_order_create_permission(
		self, get_doc, has_permission, require_authenticated_user
	):
		table = MagicMock()
		get_doc.return_value = table

		with self.assertRaises(frappe.PermissionError):
			call_restaurant_api("Restaurant Object", "T2", "add_order")

		table.check_permission.assert_called_once_with("read")
		has_permission.assert_called_once_with("Table Order", "create")
		table.add_order.assert_not_called()

	def test_make_invoice_requires_effective_pos_invoice_create_permission(self):
		order = TableOrder({"doctype": "Table Order", "name": "OR-2026-00008"})

		with (
			patch(
				"restaurant_management.restaurant_management.doctype.table_order.table_order.frappe.has_permission",
				return_value=False,
			),
			self.assertRaises(frappe.PermissionError),
		):
			order.make_invoice(mode_of_payment="Cash")

	@patch("restaurant_management.api._require_authenticated_user")
	@patch("restaurant_management.api.frappe.db.sql")
	@patch("restaurant_management.api.frappe.get_doc")
	def test_write_dispatch_locks_and_reloads_order_before_mutation(
		self, get_doc, sql, require_authenticated_user
	):
		order = MagicMock()
		order.name = "OR-2026-00004"
		order.push_item.return_value = {"saved": True}
		get_doc.return_value = order
		item = {"identifier": "ITEM-1", "qty": 1}

		result = call_restaurant_api(
			"Table Order",
			order.name,
			"push_item",
			{"item": item},
		)

		order.check_permission.assert_called_once_with("write")
		sql.assert_called_once_with(
			"SELECT name FROM `tabTable Order` WHERE name = %s FOR UPDATE",
			(order.name,),
		)
		order.reload.assert_called_once_with()
		order.push_item.assert_called_once_with(item=item)
		self.assertEqual(result, {"saved": True})

	def test_delete_item_returns_authoritative_queue_event(self):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "OR-2026-00004",
			"service_type": "Delivery",
		})
		event = {"action": "queue", "item_removed": "ITEM-1"}

		with (
			patch.object(frappe.db, "get_value", side_effect=["PLT-001", "Attending"]),
			patch.object(frappe.db, "delete") as delete,
			patch.object(frappe.db, "count", return_value=0),
			patch.object(order, "db_commit") as db_commit,
			patch.object(order, "synchronize", return_value=event) as synchronize,
		):
			result = order.delete_item("ITEM-1", unrestricted=True)

		delete.assert_called_once_with("Order Entry Item", {"identifier": "ITEM-1"})
		db_commit.assert_called_once_with()
		synchronize.assert_called_once_with({
			"action": "queue",
			"item_removed": "ITEM-1",
			"status": ["Attending"],
		})
		self.assertEqual(result, event)

	@patch("restaurant_management.api.frappe.get_installed_apps", return_value=["silent_print"])
	@patch("restaurant_management.api.frappe.db.get_single_value")
	@patch("restaurant_management.api.frappe.db.get_value")
	def test_account_print_configuration_is_complete(
		self, get_value, get_single_value, get_installed_apps
	):
		get_single_value.side_effect = lambda doctype, fieldname: {
			("Silent Print Settings", "print_user"): "Administrator",
			("Silent Print Settings", "tab_id"): "12345",
		}.get((doctype, fieldname))

		def configured_value(doctype, name, fieldname, **kwargs):
			if doctype == "Print Format":
				return frappe._dict(doc_type="Table Order", disabled=0)
			if doctype == "Silent Print Format":
				return frappe._dict(
					default_print_type="ORDER",
					page_size="Custom",
					custom_width="80mm",
					custom_height="200mm",
				)
			if doctype == "User":
				return 1

		get_value.side_effect = configured_value

		order = MagicMock()
		with patch(
			"restaurant_management.api.get_restaurant_settings",
			return_value=frappe._dict(print_format="Order Account"),
		):
			configuration = _get_account_print_configuration(order)

		self.assertEqual(configuration.print_format, "Order Account")
		self.assertEqual(configuration.print_type, "ORDER")
		self.assertEqual(configuration.print_user, "Administrator")
		self.assertEqual(configuration.tab_id, "12345")

	@patch("restaurant_management.api._get_account_print_configuration")
	@patch("restaurant_management.api.frappe.get_attr")
	@patch("restaurant_management.api.frappe.get_doc")
	def test_account_print_is_permission_checked_and_enqueued(
		self, get_doc, get_attr, get_configuration
	):
		order = MagicMock(name="OR-2026-00003", items_count=5)
		order.name = "OR-2026-00003"
		get_doc.return_value = order
		get_configuration.return_value = frappe._dict(
			print_format="Order Account",
			print_type="ORDER",
		)
		print_silently = get_attr.return_value

		result = print_order_account("OR-2026-00003")

		order.check_permission.assert_called_once_with("print")
		get_configuration.assert_called_once_with(order)
		print_silently.assert_called_once_with(
			doctype="Table Order",
			name="OR-2026-00003",
			print_format="Order Account",
			print_type="ORDER",
		)
		self.assertEqual(result["queued"], True)

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

	def test_existing_unsent_item_persists_latest_qty_without_order_time(self):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "OR-2026-00001",
			"customer": "CUSTOMER-1",
			"room_description": "Room 1",
			"table_description": "T1",
		})
		invoice = MagicMock(
			base_total_taxes_and_charges=5.34,
			grand_total=105,
		)
		invoice.items = [frappe._dict(
				item_code="PLT-001",
				item_group="PLATOS FRIOS",
				qty=3,
				rate=35,
				price_list_rate=35,
				item_tax_template="",
				item_tax_rate="{}",
				discount_percentage=12,
				discount_amount=0,
			)]
		entry = {
			"identifier": "ITEM-1",
			"item_code": "PLT-001",
			"qty": 3,
			"rate": 35,
			"price_list_rate": 35,
			"item_tax_template": "",
			"item_tax_rate": "{}",
			"discount_percentage": 12,
			"status": "Pending",
			"notes": "Sin cebolla",
			"ordered_time": "2026-07-21 07:26:46",
			"ordered_nro": 7,
			"ordered_finish": 0,
			"processing_started_at": None,
			"processing_started_by": None,
			"completed_at": None,
			"completed_by": None,
			"waiting_time_minutes": 0,
			"preparation_time_minutes": 0,
			"total_time_minutes": 0,
			"preparation_time_target": 0,
			"preparation_time_source": None,
			"has_batch_no": 0,
			"batch_no": None,
			"has_serial_no": 0,
			"serial_no": None,
		}

		with (
			patch.object(order, "get_invoice", return_value=invoice),
			patch.object(order, "validate"),
			patch.object(frappe.db, "sql", return_value=[]),
			patch.object(frappe.db, "count", return_value=1),
			patch.object(frappe.db, "set_value") as set_value,
		):
			action = order.update_item(entry)

		self.assertEqual(action, "db_commit")
		values = set_value.call_args.args[2]
		self.assertEqual(values["qty"], 3)
		self.assertEqual(values["discount_percentage"], 12)
		self.assertEqual(values["notes"], "Sin cebolla")
		self.assertEqual(values["status"], "Attending")
		self.assertIsNone(values["ordered_time"])
		self.assertEqual(values["ordered_nro"], 0)

	@patch(
		"restaurant_management.restaurant_management.restaurant_manage.check_exceptions"
	)
	def test_increment_item_adds_delta_to_persisted_unsent_qty(self, check_exceptions):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "OR-2026-00001",
			"customer": "CUSTOMER-1",
		})
		item = {
			"identifier": "ITEM-1",
			"item_code": "PLT-001",
			"qty": 1,
			"status": "Attending",
		}
		event = {"action": "Update"}

		with (
			patch.object(order, "reload") as reload_order,
			patch.object(order, "items_list", return_value=[item]),
			patch.object(order, "update_item", return_value="db_commit") as update_item,
			patch.object(order, "db_commit") as db_commit,
			patch.object(order, "synchronize", return_value=event) as synchronize,
			patch.object(frappe.db, "sql") as sql,
		):
			result = order.increment_item("ITEM-1", 2)

		self.assertEqual(result, event)
		self.assertEqual(item["qty"], 3)
		reload_order.assert_called_once_with()
		update_item.assert_called_once_with(item)
		db_commit.assert_called_once_with()
		synchronize.assert_called_once_with({"item": "ITEM-1"})
		sql.assert_called_once_with(
			"SELECT name FROM `tabTable Order` WHERE name = %s FOR UPDATE",
			("OR-2026-00001",),
		)

	@patch(
		"restaurant_management.restaurant_management.restaurant_manage.check_exceptions"
	)
	def test_update_item_details_persists_visible_note_and_discount(self, check_exceptions):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "OR-2026-00001",
			"pos_profile": "Resto",
			"entry_items": [{
				"doctype": "Order Entry Item",
				"identifier": "ITEM-1",
				"item_code": "PLT-001",
				"status": "Attending",
				"qty": 1,
				"rate": 35,
				"price_list_rate": 35,
				"discount_percentage": 0,
				"notes": "",
			}],
		})
		event = {"action": "Update", "data": {}}

		with (
			patch.object(frappe.db, "get_value", return_value=1),
			patch.object(order, "update_item", return_value="db_commit") as update_item,
			patch.object(order, "reload") as reload_order,
			patch.object(order, "aggregate") as aggregate,
			patch.object(order, "synchronize", return_value=event) as synchronize,
		):
			result = order.update_item_details(
				"ITEM-1",
				notes="Sin cebolla",
				discount_percentage=10,
				client="CLIENT-1",
			)

		entry = update_item.call_args.args[0]
		self.assertEqual(entry["notes"], "Sin cebolla")
		self.assertEqual(entry["discount_percentage"], 10)
		self.assertEqual(entry["rate"], 31.5)
		self.assertEqual(result, event)
		reload_order.assert_called_once_with()
		aggregate.assert_called_once_with()
		synchronize.assert_called_once_with({"item": "ITEM-1", "client": "CLIENT-1"})

	@patch(
		"restaurant_management.restaurant_management.restaurant_manage.check_exceptions"
	)
	def test_update_item_quantity_persists_absolute_unsent_qty(self, check_exceptions):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "OR-2026-00001",
			"entry_items": [{
				"doctype": "Order Entry Item",
				"identifier": "ITEM-1",
				"item_code": "PLT-001",
				"status": "Attending",
				"qty": 1,
				"rate": 35,
				"price_list_rate": 35,
			}],
		})
		event = {"action": "Update", "data": {}}

		with (
			patch.object(frappe.db, "sql") as sql,
			patch.object(order, "reload") as reload_order,
			patch.object(order, "update_item", return_value="db_commit") as update_item,
			patch.object(order, "aggregate") as aggregate,
			patch.object(order, "synchronize", return_value=event) as synchronize,
		):
			result = order.update_item_quantity(
				"ITEM-1", qty=4, client="CLIENT-1"
			)

		entry = update_item.call_args.args[0]
		self.assertEqual(entry["qty"], 4)
		self.assertEqual(entry["status"], "Attending")
		self.assertEqual(result, event)
		sql.assert_called_once_with(
			"SELECT name FROM `tabTable Order` WHERE name = %s FOR UPDATE",
			("OR-2026-00001",),
		)
		self.assertEqual(reload_order.call_count, 2)
		aggregate.assert_called_once_with()
		synchronize.assert_called_once_with({"item": "ITEM-1", "client": "CLIENT-1"})

	@patch(
		"restaurant_management.restaurant_management.restaurant_manage.check_exceptions"
	)
	def test_update_item_quantity_rejects_fractional_or_zero_qty(self, check_exceptions):
		order = TableOrder({
			"doctype": "Table Order",
			"name": "OR-2026-00001",
		})

		for quantity in (0, -1, 1.5):
			with self.subTest(quantity=quantity), self.assertRaises(frappe.ValidationError):
				order.update_item_quantity("ITEM-1", qty=quantity)

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
