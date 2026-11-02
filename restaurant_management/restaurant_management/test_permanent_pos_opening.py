import copy
import unittest
from unittest.mock import patch

import frappe
from frappe.utils import add_days, today, now_datetime
from datetime import timedelta
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from restaurant_management.restaurant_management.permanent_pos_opening import PermanentPOSOpeningMixin

MODULE = "restaurant_management.restaurant_management.permanent_pos_opening"


class ExtendedInvoice(PermanentPOSOpeningMixin, POSInvoice):
    pass


class TestPermanentPOSOpening(unittest.TestCase):
    def setUp(self):
        self.settings = frappe._dict(company="Test Company", pos_profile="Test Profile", allow_permanent_pos_opening=1)
        self.opening = frappe._dict(name="OPEN-TEST", company="Test Company", docstatus=1, period_start_date=add_days(today(), -400))
        self.invoice = ExtendedInvoice({"doctype": "POS Invoice", "company": "Test Company", "pos_profile": "Test Profile", "is_pos": 1})
        self.settings_mock = self.enterContext(patch(MODULE + ".get_restaurant_settings", return_value=self.settings))
        self.real_get_all = frappe.get_all
        self.openings_mock = self.enterContext(patch("frappe.get_all", side_effect=self.get_all))
        self.openings = [self.opening]

    def get_all(self, doctype, *args, **kwargs):
        if doctype == "POS Opening Entry":
            return self.openings
        return self.real_get_all(doctype, *args, **kwargs)

    def test_old_valid_opening_passes_without_mutation(self):
        before = copy.deepcopy(self.invoice.as_dict())
        opening_before = dict(self.opening)
        self.invoice.validate_pos_opening_entry()
        self.assertEqual(before, self.invoice.as_dict())
        self.assertEqual(opening_before, self.opening)
        calls = [c for c in self.openings_mock.call_args_list if c.args[0] == "POS Opening Entry"]
        self.assertEqual(calls[-1].kwargs["filters"], {"pos_profile": "Test Profile", "status": "Open"})

    def test_disabled_delegates_to_native_outdated_error(self):
        self.settings.allow_permanent_pos_opening = 0
        with self.assertRaisesRegex(frappe.ValidationError, "outdated"):
            self.invoice.validate_pos_opening_entry()

    def test_string_zero_is_disabled(self):
        self.settings.allow_permanent_pos_opening = "0"
        with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_absent_flag_is_disabled(self):
        self.settings.pop("allow_permanent_pos_opening")
        with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_missing_settings_is_disabled(self):
        self.settings_mock.return_value = None
        with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_other_profile_is_disabled(self):
        self.settings.pos_profile = "Other Profile"
        with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_other_settings_company_is_disabled(self):
        self.settings.company = "Other Company"
        with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_missing_opening_native_error(self):
        self.openings = []
        with self.assertRaisesRegex(frappe.ValidationError, "No open POS Opening Entry"):
            self.invoice.validate_pos_opening_entry()

    def test_duplicate_invalid_opening_is_not_filtered_out(self):
        self.openings = [self.opening, frappe._dict(self.opening, name="OTHER", docstatus=0, company="Other")]
        with self.assertRaisesRegex(frappe.ValidationError, "multiple open POS Opening Entries"):
            self.invoice.validate_pos_opening_entry()

    def test_unsubmitted_opening_rejected(self):
        for status in [0, 2]:
            with self.subTest(status=status):
                self.opening.docstatus = status
                with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_wrong_company_rejected(self):
        self.opening.company = "Other Company"
        with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_future_date_rejected(self):
        self.opening.period_start_date = add_days(today(), 1)
        with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_future_time_today_rejected(self):
        self.opening.period_start_date = now_datetime() + timedelta(seconds=20)
        with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_missing_start_date_rejected(self):
        self.opening.period_start_date = None
        with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_reference_mismatch_rejected(self):
        self.invoice.restaurant_pos_opening_entry = "OTHER"
        with self.assertRaises(frappe.ValidationError): self.invoice.validate_pos_opening_entry()

    def test_matching_reference_passes(self):
        self.invoice.restaurant_pos_opening_entry = self.opening.name
        self.invoice.validate_pos_opening_entry()

    def test_current_day_delegates_to_native(self):
        self.opening.period_start_date = today()
        with patch.object(SalesInvoice, "validate_pos_opening_entry", return_value="native") as native:
            self.assertEqual(self.invoice.validate_pos_opening_entry(), "native")
            native.assert_called_once()

    def test_sales_invoice_remains_native(self):
        invoice = SalesInvoice({"doctype": "Sales Invoice", "pos_profile": "Test Profile"})
        with self.assertRaises(frappe.ValidationError): invoice.validate_pos_opening_entry()

    def test_empty_profile_delegates(self):
        self.invoice.pos_profile = None
        with patch.object(SalesInvoice, "validate_pos_opening_entry") as native:
            self.invoice.validate_pos_opening_entry()
            native.assert_called_once()
