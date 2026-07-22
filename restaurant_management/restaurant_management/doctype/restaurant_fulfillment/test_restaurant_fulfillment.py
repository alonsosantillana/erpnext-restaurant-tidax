import unittest
from unittest.mock import MagicMock, patch

import frappe

from restaurant_management.restaurant_management.doctype.table_order.table_order import TableOrder
from restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment import (
    FULFILLMENT_TRANSITIONS,
    RestaurantFulfillment,
    sync_order_preparation,
)


class TestRestaurantFulfillment(unittest.TestCase):
    def test_delivery_and_pickup_have_separate_terminal_states(self):
        self.assertEqual(FULFILLMENT_TRANSITIONS["Delivery"]["Delivered"], set())
        self.assertEqual(FULFILLMENT_TRANSITIONS["Pickup"]["Picked Up"], set())
        self.assertNotIn("Picked Up", FULFILLMENT_TRANSITIONS["Delivery"]["Ready"])
        self.assertNotIn("Delivered", FULFILLMENT_TRANSITIONS["Pickup"]["Ready"])

    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment.frappe.get_doc"
    )
    def test_invoiced_order_can_continue_logistics(self, get_doc):
        get_doc.return_value = frappe._dict(
            service_type="Delivery",
            table=None,
            status="Invoiced",
            company="COMPANY",
            pos_profile="POS",
            customer="CUSTOMER",
        )
        fulfillment = RestaurantFulfillment(
            {
                "doctype": "Restaurant Fulfillment",
                "order": "OR-1",
                "fulfillment_type": "Delivery",
            }
        )

        fulfillment._validate_order_context()

        self.assertEqual(fulfillment.company, "COMPANY")
        self.assertEqual(fulfillment.pos_profile, "POS")
        self.assertEqual(fulfillment.customer, "CUSTOMER")

    def test_direct_status_edit_is_rejected(self):
        fulfillment = RestaurantFulfillment(
            {
                "doctype": "Restaurant Fulfillment",
                "status": "Ready",
                "fulfillment_type": "Delivery",
            }
        )
        previous = frappe._dict(status="Preparing")
        fulfillment.get_doc_before_save = MagicMock(return_value=previous)

        with self.assertRaises(frappe.ValidationError):
            fulfillment._validate_status_change()

    @patch(
        "restaurant_management.restaurant_management.doctype.table_order.table_order.frappe.get_cached_doc"
    )
    def test_delivery_fee_is_a_completed_non_production_line(self, get_cached_doc):
        get_cached_doc.return_value = frappe._dict(
            disabled=0, is_sales_item=1, is_stock_item=0
        )
        order = TableOrder(
            {
                "doctype": "Table Order",
                "name": "OR-1",
                "service_type": "Delivery",
                "entry_items": [],
            }
        )
        order.update_item = MagicMock(return_value="aggregate")
        order.aggregate = MagicMock()

        identifier = order.add_delivery_fee_item("DELIVERY-FEE", 8.5)

        entry = order.update_item.call_args.args[0]
        self.assertTrue(identifier.startswith("delivery_fee_"))
        self.assertEqual(entry["item_code"], "DELIVERY-FEE")
        self.assertEqual(entry["qty"], 1)
        self.assertEqual(entry["rate"], 8.5)
        self.assertEqual(entry["status"], "Completed")
        order.update_item.assert_called_once()
        self.assertTrue(order.update_item.call_args.kwargs["unrestricted"])
        order.aggregate.assert_called_once_with()

    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment.frappe.get_all"
    )
    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment.frappe.get_doc"
    )
    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment.frappe.db.get_single_value"
    )
    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment.frappe.db.get_value"
    )
    def test_sent_food_moves_new_delivery_to_preparing(
        self, get_value, get_single_value, get_doc, get_all
    ):
        get_value.return_value = "FUL-1"
        get_single_value.return_value = "DELIVERY-FEE"
        get_all.return_value = [frappe._dict(item_code="CEVICHE", status="Sent")]
        fulfillment = MagicMock(status="New")
        fulfillment._transition.return_value = {"status": "Preparing"}
        get_doc.return_value = fulfillment

        result = sync_order_preparation("OR-1")

        self.assertEqual(result, {"status": "Preparing"})
        fulfillment._transition.assert_called_once_with(
            "Preparing", expected_status="New", automatic=True
        )

    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment.frappe.get_all"
    )
    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment.frappe.get_doc"
    )
    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment.frappe.db.get_single_value"
    )
    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment.frappe.db.get_value"
    )
    def test_delivery_fee_does_not_control_preparation_status(
        self, get_value, get_single_value, get_doc, get_all
    ):
        get_value.return_value = "FUL-1"
        get_single_value.return_value = "DELIVERY-FEE"
        get_all.return_value = [
            frappe._dict(item_code="DELIVERY-FEE", status="Attending"),
            frappe._dict(item_code="CEVICHE", status="Completed"),
        ]
        fulfillment = MagicMock(status="Preparing")
        fulfillment._transition.return_value = {"status": "Ready"}
        get_doc.return_value = fulfillment

        result = sync_order_preparation("OR-1")

        self.assertEqual(result, {"status": "Ready"})
        fulfillment._transition.assert_called_once_with(
            "Ready", expected_status="Preparing", automatic=True
        )
