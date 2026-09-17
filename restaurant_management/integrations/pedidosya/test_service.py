import hashlib
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe

from restaurant_management.integrations.pedidosya import service
from restaurant_management.integrations.pedidosya.parsing import PayloadError


def _settings(**overrides):
    values = {
        "name": "PYA-SETTINGS",
        "company": "TEST COMPANY",
        "pos_profile": "TEST POS",
        "remote_id": "vendor-1",
        "integration_user": "integration@example.com",
        "integration_flow": "Indirect",
        "auto_accept": 0,
        "item_mappings": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _payload(**overrides):
    values = {
        "token": "middleware-token-1",
        "code": "PYA-ORDER-1",
        "expeditionType": "pickup",
        "products": [{"remoteCode": "PLT-001", "quantity": 1, "paidPrice": "35.00"}],
        "price": {"grandTotal": "35.00", "currency": "PEN"},
    }
    values.update(overrides)
    return values


class TestPedidosYaService(unittest.TestCase):
    def setUp(self):
        frappe.local.session = SimpleNamespace(user="Guest")
        frappe.local.db = Mock()
        self.now_patcher = patch(
            "restaurant_management.integrations.pedidosya.service.now_datetime",
            return_value="2026-09-16 12:00:00",
        )
        self.now_patcher.start()

    def tearDown(self):
        self.now_patcher.stop()
        frappe.local.__release_local__()

    def test_existing_identical_token_is_idempotent(self):
        payload = _payload()
        digest = hashlib.sha256(service._canonical_payload(payload).encode("utf-8")).hexdigest()
        frappe.db.get_value.return_value = SimpleNamespace(
            name="PYA-2026-00001", payload_digest=digest, status="Received"
        )

        result, created = service.receive_order(_settings(), payload)

        self.assertFalse(created)
        self.assertEqual(result, {"remoteOrderId": "PYA-2026-00001", "status": "Received"})

    def test_reused_token_with_different_payload_is_rejected(self):
        frappe.db.get_value.return_value = SimpleNamespace(
            name="PYA-2026-00001", payload_digest="different", status="Received"
        )

        with self.assertRaisesRegex(PayloadError, "different content"):
            service.receive_order(_settings(), _payload())

    @patch("restaurant_management.integrations.pedidosya.service._queue")
    @patch("restaurant_management.integrations.pedidosya.service.frappe.get_doc")
    def test_first_delivery_is_persisted_and_queued(self, get_doc, queue):
        frappe.db.get_value.return_value = None
        doc = Mock(name="PYA-2026-00001", status="Received")
        doc.name = "PYA-2026-00001"
        doc.status = "Received"
        get_doc.return_value = doc

        result, created = service.receive_order(_settings(), _payload())

        self.assertTrue(created)
        self.assertEqual(result["remoteOrderId"], "PYA-2026-00001")
        doc.insert.assert_called_once_with(ignore_permissions=True)
        queue.assert_called_once_with(
            "restaurant_management.integrations.pedidosya.service.process_order",
            job_id="pedidosya-import:PYA-2026-00001",
            name="PYA-2026-00001",
        )

    @patch("restaurant_management.integrations.pedidosya.service._queue")
    @patch("restaurant_management.integrations.pedidosya.service.frappe.get_doc")
    def test_unique_key_race_returns_the_existing_order(self, get_doc, queue):
        payload = _payload()
        digest = hashlib.sha256(service._canonical_payload(payload).encode("utf-8")).hexdigest()
        frappe.db.get_value.side_effect = [
            None,
            SimpleNamespace(name="PYA-2026-00002", payload_digest=digest, status="Received"),
        ]
        doc = Mock()
        doc.insert.side_effect = frappe.DuplicateEntryError
        get_doc.return_value = doc

        result, created = service.receive_order(_settings(), payload)

        self.assertFalse(created)
        self.assertEqual(result["remoteOrderId"], "PYA-2026-00002")
        queue.assert_not_called()

    @patch("restaurant_management.integrations.pedidosya.service.frappe.set_user")
    @patch("restaurant_management.integrations.pedidosya.service.frappe.get_doc")
    @patch("restaurant_management.integrations.pedidosya.service.normalize_lines", return_value=[])
    @patch("restaurant_management.integrations.pedidosya.service._create_restaurant_documents")
    def test_test_order_does_not_create_restaurant_documents(
        self, create_documents, normalize_lines, get_doc, set_user
    ):
        integration_order = Mock(
            status="Received",
            table_order=None,
            settings="PYA-SETTINGS",
            attempts=0,
            test_order=1,
        )
        integration_order.name = "PYA-2026-00003"
        integration_order.get_password.return_value = json.dumps(_payload(test=True))
        get_doc.side_effect = [integration_order, _settings()]

        service.process_order(integration_order.name)

        create_documents.assert_not_called()
        integration_order.db_set.assert_any_call(
            {"status": "Test", "processed_at": unittest.mock.ANY}
        )
        set_user.assert_any_call("integration@example.com")
        set_user.assert_any_call("Guest")

    @patch("restaurant_management.integrations.pedidosya.service.frappe.get_traceback", return_value="trace")
    @patch("restaurant_management.integrations.pedidosya.service.frappe.log_error")
    @patch("restaurant_management.integrations.pedidosya.service.frappe.set_user")
    @patch("restaurant_management.integrations.pedidosya.service.frappe.get_doc")
    @patch("restaurant_management.integrations.pedidosya.service.normalize_lines", return_value=[])
    @patch(
        "restaurant_management.integrations.pedidosya.service._create_restaurant_documents",
        side_effect=RuntimeError("creation failed"),
    )
    def test_creation_failure_rolls_back_and_marks_the_inbox_as_error(
        self, create_documents, normalize_lines, get_doc, set_user, log_error, get_traceback
    ):
        integration_order = Mock(
            status="Received",
            table_order=None,
            settings="PYA-SETTINGS",
            attempts=0,
            test_order=0,
        )
        integration_order.name = "PYA-2026-00004"
        integration_order.get_password.return_value = json.dumps(_payload())
        get_doc.side_effect = [integration_order, _settings()]
        frappe.db.exists.return_value = True

        service.process_order(integration_order.name)

        frappe.db.savepoint.assert_called_once_with("pedidosya_import")
        frappe.db.rollback.assert_called_once_with(save_point="pedidosya_import")
        frappe.db.set_value.assert_called_once_with(
            "PedidosYa Order",
            integration_order.name,
            {"status": "Error", "last_error": "creation failed"},
        )
        log_error.assert_called_once()

    @patch("restaurant_management.integrations.pedidosya.service.frappe.get_doc")
    def test_automatic_acceptance_sends_the_order_to_kitchen(self, get_doc):
        class KitchenOrder:
            def __init__(self):
                self.was_sent = False

            @property
            def send(self):
                self.was_sent = True

        doc = Mock(
            status="Imported",
            table_order="ORD-00001",
            settings="PYA-SETTINGS",
            accepted_callback_url=None,
            accepted_notified=0,
        )
        doc.name = "PYA-2026-00005"
        order = KitchenOrder()
        get_doc.side_effect = [doc, order, _settings()]

        result = service._accept(doc.name, automatic=True)

        self.assertEqual(result, "Accepted")
        self.assertTrue(order.was_sent)
        doc.db_set.assert_called_once_with(
            {"status": "Accepted", "processed_at": unittest.mock.ANY}
        )


if __name__ == "__main__":
    unittest.main()
