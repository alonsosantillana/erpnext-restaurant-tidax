import unittest
from types import SimpleNamespace

from restaurant_management.integrations.pedidosya.service import callback_payload


class TestPedidosYaCallbackPayloads(unittest.TestCase):
    def setUp(self):
        self.doc = SimpleNamespace(
            name="PYA-2026-00001",
            rejection_reason="ITEM_UNAVAILABLE",
            rejection_message="No stock",
        )
        self.settings = SimpleNamespace(default_preparation_minutes=20)

    def test_acceptance_contract(self):
        payload = callback_payload(self.doc, self.settings, "accepted")
        self.assertEqual(payload["status"], "order_accepted")
        self.assertEqual(payload["remoteOrderId"], self.doc.name)
        self.assertIn("acceptanceTime", payload)

    def test_rejection_contract(self):
        self.assertEqual(
            callback_payload(self.doc, self.settings, "rejected"),
            {"status": "order_rejected", "reason": "ITEM_UNAVAILABLE", "message": "No stock"},
        )

    def test_prepared_has_no_request_body(self):
        self.assertIsNone(callback_payload(self.doc, self.settings, "prepared"))

    def test_picked_up_contract(self):
        self.assertEqual(
            callback_payload(self.doc, self.settings, "picked_up"),
            {"status": "order_picked_up"},
        )


if __name__ == "__main__":
    unittest.main()
