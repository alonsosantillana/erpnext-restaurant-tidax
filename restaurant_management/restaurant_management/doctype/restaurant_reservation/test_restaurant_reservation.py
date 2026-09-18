import unittest
from unittest.mock import MagicMock, patch

import frappe

from restaurant_management.restaurant_management.doctype.restaurant_reservation.restaurant_reservation import (
    BLOCKING_STATUSES,
    TERMINAL_STATUSES,
    RestaurantReservation,
    get_table_reservation_summary,
    validate_table_available_for_order,
)


class TestRestaurantReservation(unittest.TestCase):
    def test_blocking_and_terminal_statuses_are_disjoint(self):
        self.assertFalse(set(BLOCKING_STATUSES).intersection(TERMINAL_STATUSES))
        self.assertIn("Seated", BLOCKING_STATUSES)
        self.assertIn("Cancelled", TERMINAL_STATUSES)

    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_reservation.restaurant_reservation.frappe.db.sql"
    )
    def test_repeated_seating_returns_existing_order(self, sql):
        reservation = MagicMock()
        reservation.name = "RES-ECS-2026-00001"
        reservation.table_order = "OR-ECS-2026-00001"

        result = RestaurantReservation.seat_and_open_order(reservation)

        self.assertEqual(
            result,
            {"table_order": "OR-ECS-2026-00001", "created": False},
        )
        reservation._check_action_permission.assert_called_once_with()
        reservation.reload.assert_called_once_with()
        sql.assert_called_once()

    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_reservation.restaurant_reservation.frappe.db.sql"
    )
    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_reservation.restaurant_reservation.frappe.db.exists",
        return_value=True,
    )
    def test_table_summary_reads_only_active_upcoming_reservations(
        self, exists, sql
    ):
        expected = frappe._dict(
            name="RES-ECS-2026-00002",
            status="Confirmed",
            guest_name="Ana",
            guest_count=4,
        )
        sql.return_value = [expected]

        result = get_table_reservation_summary(
            "TABLE-1", "ERPCLOUD SAC", "2026-09-18 18:00:00"
        )

        self.assertEqual(result, expected)
        query = sql.call_args.args[0]
        self.assertIn("r.status IN ('Pending', 'Confirmed', 'Arrived', 'Seated')", query)
        self.assertIn("r.reservation_to >= %s", query)
        exists.assert_called_once_with("DocType", "Restaurant Reservation")

    def test_invalid_direct_status_change_is_rejected(self):
        reservation = MagicMock()
        reservation.is_new.return_value = False
        reservation.status = "Confirmed"
        reservation.flags = frappe._dict()
        reservation.get_doc_before_save.return_value = frappe._dict(status="Pending")

        with self.assertRaises(frappe.ValidationError):
            RestaurantReservation._validate_status_change(reservation)


    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_reservation.restaurant_reservation.now_datetime",
        return_value=frappe.utils.get_datetime("2026-09-18 19:00:00"),
    )
    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_reservation.restaurant_reservation.get_restaurant_settings",
        return_value=frappe._dict(
            enable_reservations=1,
            reservation_preparation_minutes=15,
            reservation_cleanup_minutes=10,
        ),
    )
    @patch(
        "restaurant_management.restaurant_management.doctype.restaurant_reservation.restaurant_reservation.frappe.db.sql",
        return_value=[],
    )
    def test_reservation_order_is_excluded_from_table_block(
        self, sql, get_settings, current_time
    ):
        validate_table_available_for_order(
            "TABLE-1", "ERPCLOUD SAC", reservation="RES-ECS-2026-00001"
        )

        params = sql.call_args.args[1]
        self.assertEqual(params[2], "RES-ECS-2026-00001")
        self.assertEqual(str(params[3]), "2026-09-18 19:15:00")
        self.assertEqual(str(params[4]), "2026-09-18 18:50:00")
