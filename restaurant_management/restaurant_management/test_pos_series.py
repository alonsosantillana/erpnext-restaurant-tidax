from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.restaurant_management.pos_series import (
    autoname_pos_document,
    autoname_table_order,
    get_company_pos_series,
    get_company_table_order_series,
    get_default_pos_series,
    get_default_table_order_series,
    resolve_pos_document_company,
    resolve_table_order_company,
    validate_pos_document_series,
)


class TestPOSSeries(FrappeTestCase):
    @patch(
        "restaurant_management.restaurant_management.pos_series.frappe.db.get_value",
        return_value="ADA",
    )
    def test_default_opening_series_uses_company_abbreviation(self, get_value):
        self.assertEqual(
            get_default_pos_series("Company A", "POS Opening Entry"),
            "POS-OPE-ADA-.YYYY.-.#####",
        )

    @patch(
        "restaurant_management.restaurant_management.pos_series.get_restaurant_settings"
    )
    def test_reads_series_from_company_settings(self, get_settings):
        get_settings.return_value = frappe._dict(
            pos_opening_series="POS-OPE-ADA-.YYYY.-.#####"
        )
        self.assertEqual(
            get_company_pos_series("Company A", "POS Opening Entry"),
            "POS-OPE-ADA-.YYYY.-.#####",
        )
        get_settings.assert_called_once_with(company="Company A")

    @patch(
        "restaurant_management.restaurant_management.pos_series.make_autoname",
        return_value="POS-OPE-ADA-2026-00001",
    )
    @patch(
        "restaurant_management.restaurant_management.pos_series.get_company_pos_series",
        return_value="POS-OPE-ADA-.YYYY.-.#####",
    )
    @patch(
        "restaurant_management.restaurant_management.pos_series.resolve_pos_document_company",
        return_value="Company A",
    )
    def test_autoname_uses_resolved_company_series(
        self, resolve_company, get_series, make_name
    ):
        doc = MagicMock()
        doc.doctype = "POS Opening Entry"

        autoname_pos_document(doc)

        doc.set.assert_called_once_with(
            "restaurant_naming_series", "POS-OPE-ADA-.YYYY.-.#####"
        )
        self.assertEqual(doc.name, "POS-OPE-ADA-2026-00001")
        make_name.assert_called_once_with(
            "POS-OPE-ADA-.YYYY.-.#####", doc=doc
        )

    @patch(
        "restaurant_management.restaurant_management.pos_series.frappe.db.get_value"
    )
    def test_rejects_profile_from_another_company(self, get_value):
        get_value.return_value = "Company B"
        doc = frappe._dict(
            doctype="POS Opening Entry",
            company="Company A",
            pos_profile="POS-B",
        )
        self.assertRaises(
            frappe.ValidationError,
            resolve_pos_document_company,
            doc,
        )

    @patch(
        "restaurant_management.restaurant_management.pos_series.get_company_pos_series",
        return_value="POS-OPE-ADA-.YYYY.-.#####",
    )
    @patch(
        "restaurant_management.restaurant_management.pos_series.resolve_pos_document_company",
        return_value="Company A",
    )
    def test_rejects_client_series_override(self, resolve_company, get_series):
        doc = frappe._dict(
            doctype="POS Opening Entry",
            restaurant_naming_series="POS-OPE-ECS-.YYYY.-.#####",
        )
        self.assertRaises(
            frappe.PermissionError,
            validate_pos_document_series,
            doc,
        )

    @patch(
        "restaurant_management.restaurant_management.pos_series.frappe.db.get_value",
        return_value="ECS",
    )
    def test_default_table_order_series_uses_company_abbreviation(self, get_value):
        self.assertEqual(
            get_default_table_order_series("Company B"),
            "OR-ECS-.YYYY.-.#####",
        )

    @patch(
        "restaurant_management.restaurant_management.pos_series.get_restaurant_settings"
    )
    def test_reads_table_order_series_from_company_settings(self, get_settings):
        get_settings.return_value = frappe._dict(
            order_naming_series="OR-ADA-.YYYY.-.#####"
        )
        self.assertEqual(
            get_company_table_order_series("Company A"),
            "OR-ADA-.YYYY.-.#####",
        )
        get_settings.assert_called_once_with(company="Company A")

    @patch(
        "restaurant_management.restaurant_management.pos_series.make_autoname",
        return_value="OR-ECS-2026-00001",
    )
    @patch(
        "restaurant_management.restaurant_management.pos_series.get_company_table_order_series",
        return_value="OR-ECS-.YYYY.-.#####",
    )
    @patch(
        "restaurant_management.restaurant_management.pos_series.resolve_table_order_company",
        return_value="Company B",
    )
    def test_table_order_autoname_uses_company_series(
        self, resolve_company, get_series, make_name
    ):
        doc = frappe._dict(doctype="Table Order")

        autoname_table_order(doc)

        self.assertEqual(doc.naming_series, "OR-ECS-.YYYY.-.#####")
        self.assertEqual(doc.name, "OR-ECS-2026-00001")
        make_name.assert_called_once_with("OR-ECS-.YYYY.-.#####", doc=doc)

    @patch(
        "restaurant_management.restaurant_management.pos_series.frappe.db.get_value"
    )
    def test_table_order_rejects_cross_company_context(self, get_value):
        get_value.side_effect = ["Company A", "Company B"]
        doc = frappe._dict(
            doctype="Table Order",
            company="Company A",
            pos_profile="POS-A",
            table="TABLE-B",
        )

        self.assertRaises(
            frappe.ValidationError,
            resolve_table_order_company,
            doc,
        )
