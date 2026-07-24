from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.restaurant_management.company_settings import (
    resolve_restaurant_company,
)


class TestRestaurantCompanySettings(FrappeTestCase):
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
