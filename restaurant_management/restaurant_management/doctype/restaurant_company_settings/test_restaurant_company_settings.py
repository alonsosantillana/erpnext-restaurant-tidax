from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.restaurant_management.company_settings import (
    get_restaurant_settings,
    get_user_restaurant_company,
    resolve_restaurant_company,
)


class TestRestaurantCompanySettings(FrappeTestCase):
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.db.get_value",
        return_value="Company B",
    )
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.defaults.get_user_default",
        return_value=None,
    )
    def test_default_company_permission_recovers_missing_user_default(
        self, get_user_default, get_value
    ):
        company = get_user_restaurant_company("cashier@example.com")

        self.assertEqual(company, "Company B")
        get_user_default.assert_called_once_with(
            "company", user="cashier@example.com"
        )
        get_value.assert_called_once_with(
            "User Permission",
            {
                "user": "cashier@example.com",
                "allow": "Company",
                "is_default": 1,
                "apply_to_all_doctypes": 1,
            },
            "for_value",
        )

    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.db.get_value"
    )
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.defaults.get_user_default",
        return_value="Company A",
    )
    def test_explicit_user_default_has_priority_over_permission(
        self, get_user_default, get_value
    ):
        company = get_user_restaurant_company("cashier@example.com")

        self.assertEqual(company, "Company A")
        get_value.assert_not_called()

    @patch("restaurant_management.restaurant_management.company_settings.frappe.get_single")
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.db.get_value",
        return_value=None,
    )
    def test_missing_company_settings_does_not_use_legacy_single(
        self, get_value, get_single
    ):
        settings = get_restaurant_settings(company="Company A", required=False)

        self.assertIsNone(settings)
        get_single.assert_not_called()

    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.db.get_value"
    )
    def test_order_company_has_priority_over_user_default(self, get_value):
        get_value.return_value = "Company A"
        with patch(
            "restaurant_management.restaurant_management.company_settings.frappe.defaults.get_user_default",
            return_value="Company B",
        ):
            company = resolve_restaurant_company(order="ORDER-1")

        self.assertEqual(company, "Company A")

    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.db.get_value"
    )
    def test_rejects_pos_profile_from_another_company(self, get_value):
        get_value.side_effect = ["Company A", "Company B"]
        self.assertRaises(
            frappe.ValidationError,
            resolve_restaurant_company,
            order="ORDER-1",
            pos_profile="POS-B",
        )
