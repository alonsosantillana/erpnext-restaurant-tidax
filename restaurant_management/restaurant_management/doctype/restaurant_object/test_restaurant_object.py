# -*- coding: utf-8 -*-
# Copyright (c) 2021, Quantum Bit Core and Contributors
# See license.txt
from __future__ import unicode_literals

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from restaurant_management.api import call as restaurant_call
from restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage import (
	add_room,
	get_items,
)


class TestRestaurantObject(FrappeTestCase):
	def test_restaurant_order_requires_customer_selection(self):
		desk_form = frappe.get_doc("Desk Form", "restaurant-order-customer")
		customer_field = next(
			field for field in desk_form.desk_form_fields if field.fieldname == "customer"
		)

		self.assertEqual(customer_field.reqd, 1)

	def test_room_and_table_creation_do_not_write_debug_output(self):
		with patch("builtins.print") as print_mock:
			response = add_room(client="test-client")
			room = frappe.get_doc("Restaurant Object", response["current_room"])
			table = room.add_object("Table")

		print_mock.assert_not_called()
		self.assertEqual(response["client"], "test-client")
		self.assertTrue(any(item.name == room.name for item in response["rooms"]))
		self.assertEqual(table.type, "Table")
		self.assertEqual(
			frappe.db.get_value("Restaurant Object", table.name, "room"),
			room.name,
		)

	def test_restaurant_api_deletes_table_as_a_method(self):
		response = add_room(client="delete-test")
		room = frappe.get_doc("Restaurant Object", response["current_room"])
		table = room.add_object("Table")

		deleted = restaurant_call(
			model="Restaurant Object",
			name=table.name,
			method="_delete",
		)

		self.assertEqual(deleted["name"], table.name)
		self.assertFalse(frappe.db.exists("Restaurant Object", table.name))

	def test_add_order_returns_persisted_state_for_client_reconciliation(self):
		response = add_room(client="order-test")
		room = frappe.get_doc("Restaurant Object", response["current_room"])
		table = room.add_object("Table")

		result = frappe.get_doc("Restaurant Object", table.name).add_order(
			client="order-test",
		)

		order_data = result["data"]["order"]["data"]
		order = frappe.get_doc("Table Order", order_data["name"])
		pos_profile = frappe.get_doc("POS Profile", order.pos_profile)
		self.assertEqual(result["action"], "Add")
		self.assertEqual(result["client"], "order-test")
		self.assertEqual(order_data["table"], table.name)
		self.assertTrue(frappe.db.exists("Table Order", order_data["name"]))
		self.assertEqual(
			order.selling_price_list,
			pos_profile.selling_price_list,
		)

	@patch(
		"restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage.get_v15_pos_items",
		return_value=[],
	)
	@patch(
		"restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage._get_pos_item_group_root",
		return_value="RESTAURANTE",
	)
	def test_item_adapter_maps_legacy_request_to_v15(self, get_root, get_v15_items):
		result = get_items(
			start=0,
			page_length=40,
			price_list="Standard Selling",
			pos_profile="Test POS Profile",
			search_value="coffee",
		)

		self.assertEqual(result, {"items": []})
		get_root.assert_called_once_with("Test POS Profile")
		get_v15_items.assert_called_once_with(
			start=0,
			page_length=40,
			price_list="Standard Selling",
			item_group="RESTAURANTE",
			pos_profile="Test POS Profile",
			search_term="coffee",
		)
