# -*- coding: utf-8 -*-
# Copyright (c) 2021, Quantum Bit Core and Contributors
# See license.txt
from __future__ import unicode_literals

from unittest.mock import MagicMock, PropertyMock, call, patch

import frappe
from frappe.tests.utils import FrappeTestCase
from restaurant_management.api import (
	_create_customer_from_identity,
	_resolve_customer_group,
	call as restaurant_call,
	create_and_assign_customer,
	lookup_customer_identity,
	validate_link,
)
from restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage import (
	RestaurantManage,
	add_room,
	get_items,
)
from restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object import (
	RestaurantObject,
	production_command_batch_key,
)
from restaurant_management.restaurant_management.doctype.desk_form.desk_form import (
	search_customers,
)


class TestRestaurantObject(FrappeTestCase):
	@patch("restaurant_management.api.frappe.get_all")
	@patch("restaurant_management.api.frappe.db.get_value")
	@patch("restaurant_management.api.frappe.db.get_default")
	def test_customer_group_falls_back_from_group_default_to_used_leaf(
		self, get_default, get_value, get_all
	):
		get_default.return_value = "All Customer Groups"
		get_value.side_effect = lambda doctype, name, fieldname, **kwargs: (
			1 if name == "All Customer Groups" else 0
		)
		get_all.side_effect = [
			[],
			[frappe._dict(customer_group="Commercial", customer_count=10)],
		]

		self.assertEqual(
			_resolve_customer_group("Company", "Restaurant POS"),
			"Commercial",
		)

	@patch("restaurant_management.api._lookup_party_identity")
	@patch("restaurant_management.api._find_customer_by_tax_id")
	@patch("restaurant_management.api.frappe.has_permission", return_value=True)
	def test_customer_identity_lookup_reuses_an_existing_customer(
		self, has_permission, find_customer, lookup_party
	):
		find_customer.return_value = {
			"name": "CUST-1",
			"customer_name": "Existing Customer",
			"tax_id": "20123456789",
			"disabled": 0,
		}

		result = lookup_customer_identity("20123456789")

		self.assertEqual(result["status"], "existing")
		self.assertEqual(result["customer"]["name"], "CUST-1")
		lookup_party.assert_not_called()

	@patch("restaurant_management.api._assign_customer_to_order")
	@patch("restaurant_management.api._create_customer_from_identity")
	@patch("restaurant_management.api._lookup_party_identity")
	@patch("restaurant_management.api._find_customer_by_tax_id", return_value=None)
	@patch("restaurant_management.api.frappe.db.exists", return_value=False)
	@patch("restaurant_management.api.frappe.get_doc")
	def test_verified_customer_is_created_and_assigned_to_the_order(
		self, get_doc, db_exists, find_customer, lookup_party, create_customer, assign_customer
	):
		order = MagicMock()
		customer = MagicMock(name="customer")
		customer.name = "CUST-NEW"
		customer.customer_name = "Verified Customer"
		customer.tax_id = "20123456789"
		get_doc.return_value = order
		lookup_party.return_value = {"found": True, "tax_id": "20123456789"}
		create_customer.return_value = (customer, "ADDR-1")
		assign_customer.return_value = {"order": {"data": {"name": "ORDER-1"}}, "items": []}

		result = create_and_assign_customer("ORDER-1", "20123456789", "client-1")

		self.assertTrue(result["created"])
		self.assertEqual(result["customer"]["name"], "CUST-NEW")
		self.assertEqual(result["address"], "ADDR-1")
		order.check_permission.assert_called_once_with("write")
		assign_customer.assert_called_once_with(order, customer, "client-1")

	@patch("restaurant_management.api._resolve_customer_group", return_value="Commercial")
	@patch("restaurant_management.api.frappe.get_meta")
	@patch("restaurant_management.api.frappe.new_doc")
	@patch("restaurant_management.api.frappe.has_permission", return_value=True)
	def test_verified_ruc_maps_to_customer_and_registered_address(
		self, has_permission, new_doc, get_meta, resolve_customer_group
	):
		customer = MagicMock()
		customer.name = "CUST-NEW"
		address = MagicMock()
		address.name = "ADDR-NEW"
		new_doc.side_effect = [customer, address]
		get_meta.return_value.has_field.return_value = True
		identity = {
			"party_name": "Verified Company",
			"party_type": "Company",
			"tax_id": "20123456789",
			"document_type_label": "REGISTRO ÚNICO DE CONTRIBUYENTES",
			"document_type_code": "6",
			"registered_address": {
				"address_line1": "Av. Principal 123",
				"country": "Peru",
				"department": "LIMA",
				"province": "LIMA",
				"district": "MIRAFLORES",
				"location_code": "150122",
			},
		}

		created_customer, address_name = _create_customer_from_identity(identity)

		self.assertIs(created_customer, customer)
		self.assertEqual(address_name, "ADDR-NEW")
		self.assertEqual(customer.customer_name, "Verified Company")
		self.assertEqual(customer.customer_type, "Company")
		self.assertEqual(customer.tax_id, "20123456789")
		self.assertEqual(customer.customer_group, "Commercial")
		self.assertEqual(address.address_line1, "Av. Principal 123")
		address.append.assert_called_once_with("links", {
			"link_doctype": "Customer",
			"link_name": "CUST-NEW",
		})

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
	def test_table_people_counter_sums_active_order_guest_count(self, get_all):
		table = RestaurantObject({
			"doctype": "Restaurant Object",
			"name": "TABLE-TEST",
			"type": "Table",
		})

		self.assertEqual(table.guest_count, 5)
		get_all.assert_called_once_with("Table Order", filters={
			"table": "TABLE-TEST",
			"status": "Attending"
		}, pluck="guest_count")

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

		notification = {
			"action": "Notifications",
			"orders_count": 2,
			"current_user": "cook@example.com",
		}
		publish_realtime.assert_has_calls(
			[
				call("PC-TEST", notification, after_commit=True),
				call(
					"production_center_update",
					{"center": "PC-TEST", "orders_count": 2},
					after_commit=True,
				),
			]
		)
		self.assertEqual(publish_realtime.call_count, 2)

	@patch(
		"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.db.get_value",
		return_value="Sent",
	)
	def test_single_dish_transition_uses_one_identifier(self, get_value):
		center = RestaurantObject({"doctype": "Restaurant Object", "name": "PC-TEST"})
		with patch.object(
			center,
			"set_commands_status",
			return_value={"status": "Processing"},
		) as transition:
			result = center.set_status_command("ITEM-1", expected_status="Sent")

		transition.assert_called_once_with(identifiers=["ITEM-1"], expected_status="Sent")
		self.assertEqual(result["status"], "Processing")

	@patch(
		"restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage.frappe.get_doc"
	)
	@patch(
		"restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage.frappe.get_all",
		return_value=["PC-TEST", "PC-TEST"],
	)
	def test_status_notification_reloads_each_production_center_once(self, get_all, get_doc):
		center = get_doc.return_value

		RestaurantManage.production_center_notify(["Sent", "Processing"])

		get_all.assert_called_once_with(
			"Status Managed Production Center",
			pluck="parent",
			filters={
				"parenttype": "Restaurant Object",
				"status_managed": ("in", ["Sent", "Processing"]),
			},
		)
		get_doc.assert_called_once_with("Restaurant Object", "PC-TEST")
		center.synchronize.assert_called_once_with()

	def test_production_command_batch_key_separates_legacy_rounds(self):
		first = frappe._dict(
			parent="ORDER-1",
			ordered_nro=1,
			ordered_time="2026-07-21 10:01:02",
		)
		same_round = frappe._dict(
			parent="ORDER-1",
			ordered_nro=1,
			ordered_time="2026-07-21 10:01:55",
		)
		next_round = frappe._dict(
			parent="ORDER-1",
			ordered_nro=1,
			ordered_time="2026-07-21 10:02:01",
		)

		self.assertEqual(
			production_command_batch_key(first),
			production_command_batch_key(same_round),
		)
		self.assertNotEqual(
			production_command_batch_key(first),
			production_command_batch_key(next_round),
		)

	def test_production_command_keeps_mixed_item_states_in_one_batch(self):
		center = RestaurantObject({
			"doctype": "Restaurant Object",
			"name": "PC-TEST",
			"type": "Production Center",
		})
		items = [
			frappe._dict(
				identifier="ITEM-1",
				parent="OR-2026-00001",
				item_code="PLATE-1",
				item_name="Plate one",
				qty=1,
				notes=None,
				status="Sent",
				ordered_time="2026-07-21 10:01:02",
				ordered_nro=1,
				table_description="T1",
			),
			frappe._dict(
				identifier="ITEM-2",
				parent="OR-2026-00001",
				item_code="PLATE-2",
				item_name="Plate two",
				qty=1,
				notes=None,
				status="Processing",
				ordered_time="2026-07-21 10:01:55",
				ordered_nro=1,
				table_description="T1",
			),
		]
		orders = {
			"OR-2026-00001": frappe._dict(
				owner=None,
				cambio_mozo=None,
				cambio_mozo_nombre=None,
				table_description="T1",
				room_description="Room 1",
				comentario=None,
			)
		}

		commands = center._group_production_commands(
			items,
			orders,
			{"Sent": "Processing", "Processing": "Completed"},
		)

		self.assertEqual(len(commands), 1)
		self.assertEqual(commands[0]["status"], "Mixed")
		self.assertIsNone(commands[0]["next_status"])
		self.assertEqual(commands[0]["identifiers"], ["ITEM-1", "ITEM-2"])
		self.assertEqual(
			[(item["status"], item["next_status"]) for item in commands[0]["items"]],
			[("Sent", "Processing"), ("Processing", "Completed")],
		)

	@patch(
		"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.get_all"
	)
	def test_production_dashboard_uses_full_day_and_consolidates_completed_dishes(self, get_all):
		center = RestaurantObject({
			"doctype": "Restaurant Object",
			"name": "PC-TEST",
			"description": "Kitchen",
			"type": "Production Center",
		})
		active_item = frappe._dict(
			name="ROW-1",
			identifier="ITEM-1",
			parent="ORDER-1",
			item_code="PLATE-1",
			item_name="Plate one",
			item_group="FOOD",
			qty=1,
			status="Sent",
			ordered_time="2026-07-21 08:00:00",
			ordered_nro=1,
		)
		completed_sibling = frappe._dict(
			name="ROW-2",
			identifier="ITEM-2",
			parent="ORDER-1",
			item_code="PLATE-1",
			item_name="Plate one",
			item_group="FOOD",
			qty=2,
			status="Completed",
			ordered_time="2026-07-21 08:00:30",
			ordered_nro=1,
		)
		completed_item = frappe._dict(
			name="ROW-3",
			identifier="ITEM-3",
			parent="ORDER-1",
			item_code="PLATE-1",
			item_name="Plate one",
			item_group="FOOD",
			qty=3,
			status="Completed",
			ordered_time="2026-07-21 09:00:00",
			ordered_nro=2,
		)
		get_all.side_effect = [
			[active_item],
			[active_item, completed_sibling, completed_item],
		]
		orders = {
			"ORDER-1": frappe._dict(
				name="ORDER-1",
				owner=None,
				cambio_mozo=None,
				cambio_mozo_nombre=None,
				table_description="T1",
				room_description="Room 1",
				comentario=None,
			)
		}

		with (
			patch.object(center, "_validate_production_center"),
			patch.object(
				center,
				"_production_company_and_profile",
				return_value=("Test Company", "Test POS Profile"),
			),
			patch.object(
				center,
				"_production_status_map",
				return_value={"Sent": "Processing", "Processing": "Completed"},
			),
			patch.object(
				RestaurantObject,
				"_items_group",
				new_callable=PropertyMock,
				return_value=["FOOD"],
			),
			patch.object(center, "_production_order_data", return_value=orders),
			patch(
				"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.utils.nowdate",
				return_value="2026-07-21",
			),
			patch(
				"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.has_permission",
				return_value=True,
			),
		):
			dashboard = center.production_center_dashboard()

		daily_call = get_all.call_args_list[1]
		self.assertIn(["ordered_time", ">=", "2026-07-21"], daily_call.kwargs["filters"])
		self.assertIn(["ordered_time", "<", "2026-07-22"], daily_call.kwargs["filters"])
		self.assertEqual(daily_call.kwargs["limit_page_length"], 0)
		self.assertEqual(dashboard["period"]["date"], "2026-07-21")
		self.assertEqual(dashboard["counts"]["daily_qty"], 6)
		self.assertEqual(dashboard["counts"]["completed_qty"], 5)
		self.assertEqual(dashboard["counts"]["attended_qty"], 3)
		self.assertEqual(dashboard["consolidation"][0]["pending_qty"], 1)
		self.assertEqual(dashboard["consolidation"][0]["processing_qty"], 0)
		self.assertEqual(dashboard["consolidation"][0]["completed_qty"], 5)
		self.assertEqual(dashboard["consolidation"][0]["total_qty"], 6)
		self.assertEqual(len(dashboard["commands"]), 1)
		self.assertEqual(dashboard["commands"][0]["status"], "Mixed")
		self.assertEqual(
			dashboard["commands"][0]["identifiers"],
			["ITEM-1", "ITEM-2"],
		)
		self.assertEqual(len(dashboard["attended"]), 1)
		self.assertEqual(dashboard["attended"][0]["identifiers"], ["ITEM-3"])

	@patch(
		"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.get_doc"
	)
	@patch(
		"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.db.set_value"
	)
	@patch(
		"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.get_all"
	)
	def test_production_command_transition_updates_one_batch_atomically(
		self, get_all, set_value, get_doc
	):
		center = RestaurantObject({
			"doctype": "Restaurant Object",
			"name": "PC-TEST",
			"description": "Kitchen",
			"type": "Production Center",
		})
		entries = [
			frappe._dict(
				name="ROW-1",
				identifier="ITEM-1",
				parent="ORDER-1",
				item_group="FOOD",
				status="Sent",
				ordered_time="2026-07-21 10:00:00",
				ordered_finish=0,
			),
			frappe._dict(
				name="ROW-2",
				identifier="ITEM-2",
				parent="ORDER-1",
				item_group="FOOD",
				status="Sent",
				ordered_time="2026-07-21 10:00:00",
				ordered_finish=0,
			),
		]
		get_all.side_effect = [entries, ["ORDER-1"]]
		order = get_doc.return_value

		with (
			patch.object(center, "_validate_production_center"),
			patch.object(
				center,
				"_production_company_and_profile",
				return_value=("Test Company", "Test POS Profile"),
			),
			patch.object(
				RestaurantObject,
				"_status_managed",
				new_callable=PropertyMock,
				return_value=["Sent", "Processing"],
			),
			patch.object(
				RestaurantObject,
				"_items_group",
				new_callable=PropertyMock,
				return_value=["FOOD"],
			),
			patch.object(
				RestaurantObject,
				"_production_status_map",
				return_value={"Sent": "Processing", "Processing": "Completed"},
			),
		):
			result = center.set_commands_status(["ITEM-1", "ITEM-2"], "Sent")

		self.assertEqual(result["status"], "Processing")
		self.assertEqual(set_value.call_count, 2)
		set_value.assert_any_call("Order Entry Item", "ROW-1", {"status": "Processing"})
		set_value.assert_any_call("Order Entry Item", "ROW-2", {"status": "Processing"})
		order.synchronize.assert_called_once_with(
			{"status": ["Sent", "Processing"]}
		)

	@patch(
		"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.db.set_value"
	)
	@patch(
		"restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object.frappe.get_all"
	)
	def test_production_command_transition_rejects_stale_state(self, get_all, set_value):
		center = RestaurantObject({
			"doctype": "Restaurant Object",
			"name": "PC-TEST",
			"description": "Kitchen",
			"type": "Production Center",
		})
		get_all.return_value = [frappe._dict(
			name="ROW-1",
			identifier="ITEM-1",
			parent="ORDER-1",
			item_group="FOOD",
			status="Processing",
			ordered_time="2026-07-21 10:00:00",
			ordered_finish=0,
		)]

		with (
			patch.object(center, "_validate_production_center"),
			patch.object(
				center,
				"_production_company_and_profile",
				return_value=("Test Company", "Test POS Profile"),
			),
			patch.object(
				RestaurantObject,
				"_status_managed",
				new_callable=PropertyMock,
				return_value=["Sent", "Processing"],
			),
			patch.object(
				RestaurantObject,
				"_items_group",
				new_callable=PropertyMock,
				return_value=["FOOD"],
			),
			patch.object(
				RestaurantObject,
				"_production_status_map",
				return_value={"Sent": "Processing", "Processing": "Completed"},
			),
			self.assertRaises(frappe.ValidationError),
		):
			center.set_commands_status(["ITEM-1"], "Sent")

		set_value.assert_not_called()

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
