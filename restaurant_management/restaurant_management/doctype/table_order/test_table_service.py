"""Tests for waiter-owned delivery of completed dine-in dishes."""

import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from restaurant_management.restaurant_management.doctype.table_order.table_order import TableOrder


MODULE = "restaurant_management.restaurant_management.doctype.table_order.table_order"
def _throw(message, error_type=frappe.ValidationError):
    raise error_type(message)




class _Order(SimpleNamespace):
    def get(self, field):
        return getattr(self, field, None)

    def reload(self):
        pass

    def synchronize(self, options=None):
        pass

    def deliver_completed_items(self, identifiers, expected_modified):
        return TableOrder.deliver_completed_items(self, identifiers, expected_modified)


class TestTableService(unittest.TestCase):
    def setUp(self):
        self.order = _Order(
            name="OR-TEST-1", company="COMPANY-1", table="TABLE-1",
            status="Attending", service_type="Dine In", is_dine_in=True,
            modified="2026-09-28 10:00:00", docstatus=0, tax=10, amount=60,
        )
        self.rows = [frappe._dict(
            name="ROW-DOC-1", identifier="ROW-1", parent=self.order.name,
            parenttype="Table Order", parentfield="entry_items", status="Completed",
        )]
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch(f"{MODULE}.get_user_restaurant_company", return_value="COMPANY-1"))
        self.stack.enter_context(patch(
            "restaurant_management.restaurant_management.restaurant_manage.check_exceptions",
            return_value=True,
        ))
        self.stack.enter_context(patch.object(self.order, "reload"))
        self.synchronize = self.stack.enter_context(patch.object(self.order, "synchronize"))
        self.db = MagicMock()
        self.sql = self.db.sql
        self.set_value = self.db.set_value
        self.get_all = MagicMock(return_value=self.rows)
        self.fake_frappe = SimpleNamespace(
            session=SimpleNamespace(user="waiter@example.com"),
            db=self.db, get_all=self.get_all,
            utils=SimpleNamespace(
                get_datetime=frappe.utils.get_datetime,
                now_datetime=lambda: "2026-09-28 10:01:00",
            ),
            get_roles=MagicMock(return_value=["resto_mozo"]),
            has_permission=MagicMock(return_value=True),
            throw=_throw, PermissionError=frappe.PermissionError,
            ValidationError=frappe.ValidationError,
        )
        self.stack.enter_context(patch(f"{MODULE}._", side_effect=lambda message: message))
        self.stack.enter_context(patch(f"{MODULE}.frappe", self.fake_frappe))

    def test_completed_row_is_delivered_without_other_writes(self):
        result = self.order.deliver_completed_items(["ROW-1"], str(self.order.modified))

        self.assertEqual(result, {
            "updated": ["ROW-1"], "previous_status": "Completed", "status": "Delivered",
        })
        self.set_value.assert_any_call("Order Entry Item", "ROW-DOC-1", "status", "Delivered")
        self.assertEqual(self.set_value.call_count, 2)
        self.synchronize.assert_called_once_with({"action": "Update"})

    def test_rejects_foreign_or_uncompleted_row(self):
        for change in ({"parent": "OTHER-ORDER"}, {"status": "Sent"}, {"status": "Delivered"}):
            with self.subTest(change=change):
                self.rows[0].update(change)
                with self.assertRaises(frappe.ValidationError):
                    self.order.deliver_completed_items(["ROW-1"], str(self.order.modified))
                self.set_value.assert_not_called()
                self.synchronize.assert_not_called()
                self.rows[0].update({"parent": self.order.name, "status": "Completed"})

    def test_rejects_stale_version_and_duplicate_identifiers(self):
        with self.assertRaises(frappe.ValidationError):
            self.order.deliver_completed_items(["ROW-1"], "2026-09-28 09:00:00")
        with self.assertRaises(frappe.ValidationError):
            self.order.deliver_completed_items(["ROW-1", "ROW-1"], str(self.order.modified))
        self.set_value.assert_not_called()

    def test_rejects_non_waiter(self):
        with patch.object(self.fake_frappe, "get_roles", return_value=["resto_cocina"]):
            with self.assertRaises(frappe.PermissionError):
                self.order.deliver_completed_items(["ROW-1"], str(self.order.modified))
        self.sql.assert_not_called()
        self.set_value.assert_not_called()

    def test_rejects_lost_permissions_and_company_change(self):
        with patch.object(self.fake_frappe, "has_permission", return_value=False):
            with self.assertRaises(frappe.PermissionError):
                self.order.deliver_completed_items(["ROW-1"], str(self.order.modified))
        with patch(
            f"{MODULE}.get_user_restaurant_company",
            side_effect=["COMPANY-1", "OTHER-COMPANY"],
        ):
            with self.assertRaises(frappe.PermissionError):
                self.order.deliver_completed_items(["ROW-1"], str(self.order.modified))
        self.set_value.assert_not_called()
        self.synchronize.assert_not_called()


if __name__ == "__main__":
    unittest.main()
