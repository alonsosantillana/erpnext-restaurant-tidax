# -*- coding: utf-8 -*-
# Copyright (c) 2021, Quantum Bit Core and Contributors
# See license.txt
from __future__ import unicode_literals

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage import add_room


class TestRestaurantObject(FrappeTestCase):
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
