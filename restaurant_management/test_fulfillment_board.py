"""Read-only board contracts with an in-memory query fixture, no Frappe site."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe

from restaurant_management import api


def _throw(message, exc=frappe.ValidationError, **kwargs):
    raise exc(message)


def pickup(name, status="Picked Up", payment="Paid", completed="2026-10-26 12:00:00", **values):
    row = frappe._dict(
        name=name, order=f"ORDER-{name}", company="TEST COMPANY", pos_profile="TEST POS",
        fulfillment_type="Pickup", status=status, payment_status=payment,
        customer_name_snapshot="TEST CUSTOMER", order_channel="PedidosYa",
        payment_timing="Prepaid", creation="2026-10-01 12:00:00",
        modified="2026-10-26 15:00:00", amount=38, allowed=True,
        history=[] if completed is None else [frappe._dict(
            parenttype="Restaurant Fulfillment", parentfield="status_log",
            to_status="Picked Up", changed_at=completed,
        )],
    )
    row.update(values)
    return row


class TestFulfillmentBoard(unittest.TestCase):
    def setUp(self):
        frappe.local.db = Mock()
        frappe.local.flags = frappe._dict()
        frappe.local.session = frappe._dict(user="test@example.test")
        self.addCleanup(frappe.local.__release_local__)
        self.enterContext(patch.object(frappe, "connect", side_effect=AssertionError("No site DB")))
        self.enterContext(patch.object(frappe, "throw", side_effect=_throw))
        self.enterContext(patch.object(api, "_", side_effect=lambda message: message))
        self.permission = self.enterContext(patch.object(frappe, "has_permission", return_value=True))
        self.context = self.enterContext(patch.object(
            api, "_active_restaurant_pos_context",
            return_value=("TEST COMPANY", SimpleNamespace(name="TEST POS")),
        ))
        self.list_query = self.enterContext(patch.object(frappe, "get_list", side_effect=self._get_list))
        self.all_query = self.enterContext(patch.object(frappe, "get_all", side_effect=self._get_all))
        self.rows = []

    @staticmethod
    def _matches(row, field, operator, value):
        actual = row.get(field)
        if operator == "=":
            return actual == value
        if operator == "!=":
            return actual != value
        if operator == ">=":
            return actual is not None and actual >= value
        if operator == "<":
            return actual is not None and actual < value
        raise AssertionError(f"Unexpected query operator: {operator}")

    def _select(self, filters, or_filters=None):
        if isinstance(filters, dict):
            parent_filters = [(field, *(value if isinstance(value, tuple) else ("=", value)))
                              for field, value in filters.items()]
            child_filters = []
        else:
            parent_filters = [(field, operator, value) for doctype, field, operator, value in filters
                              if doctype == "Restaurant Fulfillment"]
            child_filters = [(field, operator, value) for doctype, field, operator, value in filters
                             if doctype == "Restaurant Fulfillment Status Log"]
        return [row for row in self.rows
                if all(self._matches(row, *condition) for condition in parent_filters)
                and (not or_filters or any(self._matches(row, *condition) for condition in or_filters))
                and (not child_filters or any(
                    all(self._matches(event, *condition) for condition in child_filters)
                    for event in row.history
                ))]

    def _get_list(self, doctype, *, filters, fields, or_filters=None, limit_page_length=200, **kwargs):
        self.assertEqual(doctype, "Restaurant Fulfillment")
        # Model parent row permissions. Actual ORM/permission joins require staging.
        rows = [row for row in self._select(filters, or_filters) if row.allowed]
        return [frappe._dict({field: row.get(field) for field in fields})
                for row in rows[:limit_page_length]]

    def _get_all(self, doctype, *, filters, fields, or_filters=None, **kwargs):
        if doctype == "Restaurant Fulfillment":
            self.assertEqual(fields, ["count(name) as total"])
            return [frappe._dict(total=len(self._select(filters, or_filters)))]
        self.assertEqual(doctype, "Table Order")
        names = filters["name"][1]
        return [frappe._dict(name=row.order, amount=row.amount, status="Attending")
                for row in self.rows if row.order in names]

    def board(self, **kwargs):
        return api.get_fulfillment_board("Pickup", completed_date="2026-10-26", **kwargs)

    def names(self, rows):
        return {row["name"] for row in rows}

    def test_paid_pickup_today_is_visible_but_not_pending(self):
        self.rows = [pickup("TODAY"), pickup("OLD-PENDING", "Preparing", "Unpaid", None),
                     pickup("OLD-UNPAID", payment="Unpaid", completed="2026-10-20 12:00:00")]
        self.assertEqual(self.names(self.board()), {"TODAY", "OLD-PENDING", "OLD-UNPAID"})
        self.assertEqual(api.get_fulfillment_counts(), {"Delivery": 0, "Pickup": 2})
        frappe.db.set_value.assert_not_called()
        frappe.db.commit.assert_not_called()

    def test_completion_event_not_creation_or_modified_controls_day(self):
        self.rows = [pickup("YESTERDAY", completed="2026-10-25 12:00:00"),
                     pickup("CREATED-EARLIER"), pickup("NO-AUDIT", completed=None)]
        self.assertEqual(self.names(self.board()), {"CREATED-EARLIER"})

    def test_day_is_start_inclusive_and_next_midnight_exclusive(self):
        self.rows = [pickup("START", completed="2026-10-26 00:00:00"),
                     pickup("END", completed="2026-10-26 23:59:59.999999"),
                     pickup("NEXT", completed="2026-10-27 00:00:00")]
        self.assertEqual(self.names(self.board()), {"START", "END"})

    def test_selected_previous_date_is_supported(self):
        self.rows = [pickup("TODAY"), pickup("YESTERDAY", completed="2026-10-25 15:00:00")]
        rows = api.get_fulfillment_board("Pickup", completed_date="2026-10-25")
        self.assertEqual(self.names(rows), {"YESTERDAY"})

    def test_both_queries_keep_company_pos_type_and_row_access(self):
        self.rows = [pickup("PERMITTED"), pickup("OTHER-COMPANY", company="OTHER"),
                     pickup("OTHER-POS", pos_profile="OTHER"), pickup("NOT-PERMITTED", allowed=False),
                     pickup("DELIVERY", fulfillment_type="Delivery"),
                     pickup("CANCELLED", status="Cancelled")]
        self.assertEqual(self.names(self.board()), {"PERMITTED"})
        self.assertEqual(self.list_query.call_count, 2)
        closed = self.list_query.call_args.kwargs
        self.assertTrue(closed["distinct"])
        self.assertIn(["Restaurant Fulfillment", "company", "=", "TEST COMPANY"], closed["filters"])
        self.assertIn(["Restaurant Fulfillment", "pos_profile", "=", "TEST POS"], closed["filters"])
        self.assertIn(["Restaurant Fulfillment Status Log", "to_status", "=", "Picked Up"], closed["filters"])
        self.assertNotIn("ignore_permissions", closed)
        self.assertEqual(self.all_query.call_args.kwargs["filters"], {"name": ("in", ["ORDER-PERMITTED"])})

    def test_pending_and_completed_have_independent_limits(self):
        self.rows = [pickup(f"ACTIVE-{i}", "Ready", "Paid", None) for i in range(205)]
        self.rows += [pickup("CLOSED")]
        rows = self.board()
        self.assertEqual(len(rows), 201)
        self.assertIn("CLOSED", self.names(rows))
        self.assertEqual(api.get_fulfillment_counts()["Pickup"], 205)

    def test_duplicate_completed_rows_are_deduplicated(self):
        self.rows = [pickup("CLOSED")]
        select = self.list_query.side_effect

        def duplicated(*args, **kwargs):
            rows = select(*args, **kwargs)
            return rows + rows if kwargs.get("distinct") else rows

        self.list_query.side_effect = duplicated
        self.assertEqual(len(self.board()), 1)

    def test_legacy_without_date_remains_pending_only(self):
        self.rows = [pickup("CLOSED"), pickup("READY", "Ready", "Paid", None)]
        self.assertEqual(self.names(api.get_fulfillment_board("Pickup")), {"READY"})
        self.assertEqual(self.list_query.call_count, 1)

    def test_include_closed_preserves_historical_contract(self):
        self.rows = [pickup("CLOSED", completed="2026-10-20 12:00:00"),
                     pickup("CANCELLED", status="Cancelled")]
        self.assertEqual(self.names(self.board(include_closed=1)), {"CLOSED", "CANCELLED"})
        self.assertEqual(self.list_query.call_count, 1)

    def test_delivery_does_not_gain_completion_filter(self):
        self.rows = [pickup("DELIVERY-CLOSED", "Delivered", fulfillment_type="Delivery"),
                     pickup("DELIVERY-READY", "Ready", fulfillment_type="Delivery")]
        rows = api.get_fulfillment_board("Delivery", completed_date="invalid-not-used")
        self.assertEqual(self.names(rows), {"DELIVERY-READY"})
        self.assertEqual(self.list_query.call_count, 1)

    def test_invalid_dates_are_rejected_without_querying_rows(self):
        for value in ("2026-02-30", "26/10/2026", "20261026", "9999-12-31", "x", True, ["2026-10-26"]):
            with self.subTest(value=value), self.assertRaises(frappe.ValidationError):
                api.get_fulfillment_board("Pickup", completed_date=value)
        self.list_query.assert_not_called()

    def test_guest_and_missing_read_permission_are_rejected(self):
        frappe.local.session.user = "Guest"
        with self.assertRaises(frappe.AuthenticationError):
            self.board()
        frappe.local.session.user = "test@example.test"
        self.permission.return_value = False
        with self.assertRaises(frappe.PermissionError):
            self.board()
        self.context.assert_not_called()
        self.list_query.assert_not_called()

    def test_invalid_type_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            api.get_fulfillment_board("Other", completed_date="2026-10-26")
        self.list_query.assert_not_called()

    def test_payload_remains_minimized_and_includes_original_amount(self):
        self.rows = [pickup("CLOSED", contact_phone="PRIVATE", instructions="PRIVATE")]
        row = self.board()[0]
        self.assertEqual(row["amount"], 38)
        for field in ("history", "contact_phone", "instructions", "company", "allowed"):
            self.assertNotIn(field, row)
