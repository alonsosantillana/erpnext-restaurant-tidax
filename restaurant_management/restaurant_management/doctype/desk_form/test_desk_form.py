# -*- coding: utf-8 -*-
# Copyright (c) 2024, AlphaBit Technology and contributors and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDeskForm(FrappeTestCase):
	def test_payment_order_has_no_pos_awesome_delivery_charge_fetch(self):
		desk_form = frappe.get_doc("Desk Form", "payment-order")
		delivery_charges = next(
			field
			for field in desk_form.desk_form_fields
			if field.fieldname == "delivery_charges"
		)

		self.assertFalse(delivery_charges.fetch_from)
