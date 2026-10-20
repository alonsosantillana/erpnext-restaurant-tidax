from contextlib import ExitStack
from unittest import TestCase
from unittest.mock import MagicMock, patch

import frappe

from restaurant_management.patches.v15_0 import migrate_restaurant_company_settings as migration


class TestMigrateRestaurantCompanySettings(TestCase):
    def setUp(self):
        stack = self.enterContext(ExitStack())
        self.db = stack.enter_context(patch.object(migration.frappe, "db", MagicMock()))
        self.db.exists.return_value = False
        self.db.get_value.side_effect = self.get_db_value
        self.values = {}
        self.target = MagicMock()
        self.target.doctype = "Restaurant Company Settings"
        self.target.name = None
        self.target.flags = frappe._dict()
        self.target.get.side_effect = self.values.get
        self.target.set.side_effect = self.values.__setitem__
        self.target.insert.side_effect = self.check_mandatory_series
        self.new_doc = stack.enter_context(
            patch.object(migration.frappe, "new_doc", return_value=self.target)
        )
        self.legacy = frappe._dict(pos_profile="POS-LEGACY", print_format_order="Order")
        self.get_single = stack.enter_context(
            patch.object(migration.frappe, "get_single", return_value=self.legacy)
        )
        stack.enter_context(
            patch.object(
                migration.frappe,
                "get_meta",
                return_value=frappe._dict(fields=[frappe._dict(fieldname="user")]),
            )
        )

    def get_db_value(self, doctype, *args, **kwargs):
        if doctype == "Company":
            return "QSAC"
        if doctype == "POS Profile":
            return "Company A"
        return None

    def check_mandatory_series(self, **kwargs):
        for fieldname in (
            "order_naming_series",
            "expense_naming_series",
            "pos_opening_series",
            "pos_closing_series",
            "reservation_naming_series",
        ):
            if not self.values.get(fieldname):
                raise frappe.MandatoryError(fieldname)

    def test_missing_series_are_ready_before_insert(self):
        migration._migrate_settings("Company A")

        for fieldname, prefix in (
            ("order_naming_series", "OR"),
            ("expense_naming_series", "GTO"),
            ("pos_opening_series", "POS-OPE"),
            ("pos_closing_series", "POS-CLO"),
            ("reservation_naming_series", "RES"),
        ):
            self.assertEqual(self.values[fieldname], f"{prefix}-QSAC-.YYYY.-.#####")
        self.assertEqual(self.target.company, "Company A")
        self.assertTrue(self.target.flags.restaurant_settings_migration)
        self.assertEqual(self.values["pos_profile"], "POS-LEGACY")
        self.target.insert.assert_called_once_with(ignore_permissions=True)

    def test_repeat_run_does_not_replace_existing_settings(self):
        self.db.exists.return_value = True

        migration._migrate_settings("Company A")

        self.new_doc.assert_not_called()
        self.get_single.assert_not_called()
        self.target.insert.assert_not_called()

    def test_preconfigured_series_are_preserved(self):
        self.values["order_naming_series"] = "CUSTOM-QSAC-.YYYY.-.#####"

        migration._migrate_settings("Company A")

        self.assertEqual(self.values["order_naming_series"], "CUSTOM-QSAC-.YYYY.-.#####")
        self.target.insert.assert_called_once_with(ignore_permissions=True)

    def test_pos_profile_from_another_company_is_not_copied(self):
        migration._migrate_settings("Company B")

        self.assertNotIn("pos_profile", self.values)
        self.assertEqual(self.target.company, "Company B")
        self.target.insert.assert_called_once_with(ignore_permissions=True)

    def test_legacy_exception_rows_are_still_copied(self):
        self.legacy.restaurant_exceptions = [
            frappe._dict(user="waiter@example.com", ignored_field="not a child field")
        ]

        migration._migrate_settings("Company A")

        self.target.append.assert_called_once_with(
            "restaurant_exceptions", {"user": "waiter@example.com"}
        )
