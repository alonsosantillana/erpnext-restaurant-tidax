import unittest
from types import SimpleNamespace

from restaurant_management.integrations.pedidosya.parsing import (
    PayloadError,
    address_snapshot,
    delivery_mode,
    delivery_fee,
    external_total,
    normalize_lines,
)


class TestPedidosYaParsing(unittest.TestCase):
    def setUp(self):
        self.mappings = {
            "PLT-001": SimpleNamespace(item_code="PLT-001"),
            "TOP-001": SimpleNamespace(item_code="MAT-TOPPING"),
        }

    def test_platform_delivery_allows_missing_address(self):
        payload = {"expeditionType": "delivery", "delivery": {"riderPickupTime": "2026-09-16T10:00:00Z"}}
        self.assertEqual(delivery_mode(payload), ("Delivery", "PedidosYa"))
        self.assertEqual(address_snapshot(payload), "")

    def test_vendor_delivery_and_address(self):
        payload = {
            "expeditionType": "delivery",
            "delivery": {"address": {"street": "Av. Lima", "number": "100", "city": "Lima"}},
        }
        self.assertEqual(delivery_mode(payload), ("Delivery", "Restaurant"))
        self.assertEqual(address_snapshot(payload), "Av. Lima, 100, Lima")

    def test_product_and_topping_are_mapped_with_paid_prices(self):
        payload = {
            "products": [{
                "remoteCode": "PLT-001",
                "quantity": 2,
                "paidPrice": "30.00",
                "selectedToppings": [{"remoteCode": "TOP-001", "quantity": 1, "price": "2.50"}],
            }]
        }
        lines = normalize_lines(payload, self.mappings)
        self.assertEqual(str(lines[0]["rate"]), "12.50")
        self.assertEqual(str(lines[1]["qty"]), "2")
        self.assertEqual(str(lines[1]["rate"]), "2.50")

    def test_unmapped_remote_code_is_rejected(self):
        with self.assertRaisesRegex(PayloadError, "UNKNOWN"):
            normalize_lines({"products": [{"remoteCode": "UNKNOWN", "quantity": 1}]}, self.mappings)

    def test_external_total_uses_documented_price_container(self):
        self.assertEqual(str(external_total({"price": {"grandTotal": "42.10"}})), "42.10")

    def test_delivery_fee_defaults_to_zero(self):
        self.assertEqual(str(delivery_fee({"price": {}})), "0")
        self.assertEqual(str(delivery_fee({"price": {"deliveryFee": "4.90"}})), "4.90")
        self.assertEqual(
            str(delivery_fee({"price": {"deliveryFees": [{"name": "delivery", "value": 3}, {"name": "bag", "value": 1.5}]}})),
            "4.5",
        )


if __name__ == "__main__":
    unittest.main()
