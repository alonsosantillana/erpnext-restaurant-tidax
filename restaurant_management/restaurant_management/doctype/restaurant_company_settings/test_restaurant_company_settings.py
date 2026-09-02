from unittest.mock import MagicMock, call, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.restaurant_management.company_settings import (
    get_restaurant_payment_permissions,
    get_restaurant_settings,
    get_user_restaurant_company,
    resolve_restaurant_company,
)


class TestRestaurantCompanySettings(FrappeTestCase):
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.get_meta"
    )
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.db.get_value"
    )
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.has_permission",
        return_value=False,
    )
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.get_roles",
        return_value=["resto_mozo"],
    )
    def test_waiter_payment_permission_is_limited_to_own_orders(
        self, get_roles, has_permission, get_value, get_meta
    ):
        meta = MagicMock()
        meta.has_field.return_value = True
        get_meta.return_value = meta
        get_value.return_value = frappe._dict(
            allow_restaurant_payment=1,
            allow_restaurant_payment_for_others=0,
        )

        own_order = get_restaurant_payment_permissions(
            "POS Restaurant",
            user="waiter@example.com",
            order_owner="waiter@example.com",
        )
        other_order = get_restaurant_payment_permissions(
            "POS Restaurant",
            user="waiter@example.com",
            order_owner="other@example.com",
        )

        self.assertTrue(own_order.can_pay)
        self.assertFalse(own_order.can_pay_other_orders)
        self.assertFalse(other_order.can_pay)

    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.get_meta"
    )
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.db.get_value"
    )
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.has_permission",
        return_value=False,
    )
    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.get_roles",
        return_value=["resto_mozo"],
    )
    def test_waiter_can_be_configured_to_collect_other_orders(
        self, get_roles, has_permission, get_value, get_meta
    ):
        meta = MagicMock()
        meta.has_field.return_value = True
        get_meta.return_value = meta
        get_value.return_value = frappe._dict(
            allow_restaurant_payment=1,
            allow_restaurant_payment_for_others=1,
        )

        permissions = get_restaurant_payment_permissions(
            "POS Restaurant",
            user="waiter@example.com",
            order_owner="other@example.com",
        )

        self.assertTrue(permissions.can_pay)
        self.assertTrue(permissions.can_pay_other_orders)

    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.db.get_value"
    )
    def test_default_company_permission_recovers_missing_user_default(
        self, get_value
    ):
        get_value.side_effect = [None, "Company B"]

        company = get_user_restaurant_company("cashier@example.com")

        self.assertEqual(company, "Company B")
        self.assertEqual(
            get_value.call_args_list,
            [
                call(
                    "DefaultValue",
                    {"parent": "cashier@example.com", "defkey": "company"},
                    "defvalue",
                ),
                call(
                    "User Permission",
                    {
                        "user": "cashier@example.com",
                        "allow": "Company",
                        "is_default": 1,
                        "apply_to_all_doctypes": 1,
                    },
                    "for_value",
                ),
            ],
        )

    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.db.get_value",
        return_value="Company A",
    )
    def test_explicit_user_default_has_priority_over_permission(self, get_value):
        company = get_user_restaurant_company("cashier@example.com")

        self.assertEqual(company, "Company A")
        get_value.assert_called_once_with(
            "DefaultValue",
            {"parent": "cashier@example.com", "defkey": "company"},
            "defvalue",
        )

    @patch(
        "restaurant_management.restaurant_management.company_settings.frappe.db.get_value",
        return_value=None,
    )
    def test_missing_explicit_company_does_not_use_global_default(self, get_value):
        company = get_user_restaurant_company("kitchen@example.com")

        self.assertIsNone(company)
        self.assertEqual(get_value.call_count, 2)

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
