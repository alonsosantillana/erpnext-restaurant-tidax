import unittest
from types import SimpleNamespace
from unittest.mock import patch

from restaurant_management.integrations.pedidosya.client import validate_callback_url


class TestPedidosYaCallbackSecurity(unittest.TestCase):
    def setUp(self):
        self.settings = SimpleNamespace(
            api_base_url="https://integration-middleware.stg.restaurant-partners.com",
            callback_allowed_hosts="callbacks.example.com",
        )

    def test_allows_exact_configured_https_host(self):
        self.assertEqual(
            validate_callback_url(self.settings, "https://callbacks.example.com/order/1"),
            "https://callbacks.example.com/order/1",
        )

    @patch("restaurant_management.integrations.pedidosya.client._", side_effect=lambda value: value)
    @patch("frappe.throw", side_effect=ValueError("blocked"))
    def test_blocks_private_callback_target(self, throw, translate):
        with self.assertRaisesRegex(ValueError, "blocked"):
            validate_callback_url(self.settings, "https://127.0.0.1/order/1")

    @patch("restaurant_management.integrations.pedidosya.client._", side_effect=lambda value: value)
    @patch("frappe.throw", side_effect=ValueError("blocked"))
    def test_blocks_host_suffix_confusion(self, throw, translate):
        with self.assertRaisesRegex(ValueError, "blocked"):
            validate_callback_url(self.settings, "https://callbacks.example.com.attacker.test/order/1")


if __name__ == "__main__":
    unittest.main()
