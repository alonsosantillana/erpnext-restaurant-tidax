# -*- coding: utf-8 -*-
# Copyright (c) 2021, Quantum Bit Core and Contributors
# See license.txt
from __future__ import unicode_literals

from unittest.mock import PropertyMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase
from restaurant_management.api import call as restaurant_call, validate_link
from restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage import (
	add_room,
	get_items,
)
from restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object import (
	RestaurantObject,
)
from restaurant_management.restaurant_management.doctype.desk_form.desk_form import (
	search_customers,
)


class TestRestaurantObject(FrappeTestCase):
	@patch("restaurant_management.api.frappe.db.get_value", return_value="Ana Perez")
	@patch(
		"restaurant_management.api.frappe.get_list",
		return_value=[frappe._dict(name="waiter@example.com")],
	)
	@patch("restaurant_management.api.frappe.has_permission", return_value=True)
	def test_single_link_fetch_returns_the_full_value(
		self, has_permission, get_list, get_value
	):
		self.assertEqual(
			validate_link("waiter@example.com", "User", "full_name"),
			"Ok",
		)
		self.assertEqual(frappe.response["fetch_values"], ["Ana Perez"])
		has_permission.assert_called_once_with("User", "read")
		get_value.assert_called_once_with("User", "waiter@example.com", ["full_name"])

	@patch(
		"restaurant_management.restaurant_management.doctype.desk_form.desk_form.frappe.get_list"
	)
	@patch(
		"restaurant_management.restaurant_management.doctype.desk_form.desk_form.frappe.has_permission",
		return_value=True,
	)
	def test_customer_link_search_includes_tax_id(self, has_permission, get_list):
		get_list.return_value = [["CUSTOMER-1", "Customer One", "20123456789"]]

		result = search_customers("Customer", "201234", "name", 0, 10, {})

		self.assertEqual(result, get_list.return_value)
		has_permission.assert_called_once_with("Customer", "read")
		self.assertIn(
			["Customer", "tax_id", "like", "%201234%"],
			get_list.call_args.kwargs["or_filters"],
		)
		self.assertEqual(
			get_list.call_args.kwargs["fields"],
			["name", "customer_name", "tax_id"],
		)
		self.assertEqual(get_list.call_args.kwargs["filters"], {"disabled": 0})

	@patch(
		"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.get_all"
	)
	def test_table_counter_sums_ordered_item_quantities(self, get_all):
		get_all.side_effect = [["ORDER-1"], [2, 1, 3]]
		table = RestaurantObject({
			"doctype": "Restaurant Object",
			"name": "TABLE-TEST",
			"type": "Table",
		})

		self.assertEqual(table.ordered_items_qty, 6)
		self.assertEqual(get_all.call_count, 2)

	@patch(
		"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.get_all",
		return_value=[2, 3],
	)
	def test_table_people_counter_sums_active_order_dinners(self, get_all):
		table = RestaurantObject({
			"doctype": "Restaurant Object",
			"name": "TABLE-TEST",
			"type": "Table",
		})

		self.assertEqual(table.dinners_count, 5)
		get_all.assert_called_once_with("Table Order", filters={
			"table": "TABLE-TEST",
			"status": "Attending"
		}, pluck="dinners")

	def test_unsent_item_status_uses_mustard_pending_message(self):
		for status in ("Pending", "Attending"):
			status_data = RestaurantObject._status(status)

			self.assertEqual(status_data["color"], "#D49B00")
			self.assertEqual(status_data["message"], frappe._("Pending to send"))

	@patch(
		"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.publish_realtime"
	)
	def test_production_center_notification_is_published_after_commit(self, publish_realtime):
		center = RestaurantObject({
			"doctype": "Restaurant Object",
			"name": "PC-TEST",
			"type": "Production Center",
			"current_user": "cook@example.com",
		})

		with patch.object(
			RestaurantObject,
			"orders_count_in_production_center",
			new_callable=PropertyMock,
			return_value=2,
		):
			center.synchronize()

		publish_realtime.assert_called_once_with(
			"PC-TEST",
			{
				"action": "Notifications",
				"orders_count": 2,
				"current_user": "cook@example.com",
			},
			after_commit=True,
		)

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
