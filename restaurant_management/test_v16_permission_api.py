"""Permission-call regression tests; never submit, print or contact a provider."""

import unittest
from unittest.mock import patch

import frappe
from frappe.permissions import has_permission as native_has_permission
from restaurant_management import printing, electronic_invoice


class TestV16PermissionAPI(unittest.TestCase):
    def setUp(self):
        self.invoice = frappe._dict(doctype="POS Invoice", name="TEST-PINV", company="Test Company", pos_profile="Test POS", owner="owner@example.invalid")
        self.order = frappe._dict(pos_profile="Order POS", owner="owner@example.invalid", cambio_mozo="waiter@example.invalid")
        self.print_permission = self.enterContext(patch.object(printing, "has_permission", autospec=True, return_value=True))
        self.electronic_permission = self.enterContext(patch.object(electronic_invoice, "has_permission", autospec=True, return_value=True))
        self.get_doc = self.enterContext(patch.object(frappe, "get_doc", return_value=self.invoice))
        self.get_value = self.enterContext(patch.object(frappe.db, "get_value", return_value=self.order))
        self.queue = self.enterContext(patch.object(printing, "enqueue_print", autospec=True, return_value={"queued": True}))
        self.print_fallback = self.enterContext(patch.object(printing, "get_restaurant_payment_permissions", return_value=frappe._dict(can_pay=False)))
        self.electronic_fallback = self.enterContext(patch.object(electronic_invoice, "get_restaurant_payment_permissions", return_value=frappe._dict(can_pay=False)))
        self.linked_order = self.enterContext(patch.object(electronic_invoice, "_get_linked_order", return_value=self.order))

    def test_native_print_grant_preserves_manual_request(self):
        self.assertTrue(printing.queue_invoice_print(self.invoice.name, "manual-1")["queued"])
        self.print_permission.assert_called_once_with("POS Invoice", "print", self.invoice, print_logs=False)
        self.print_fallback.assert_not_called()
        self.queue.assert_called_once_with("POS Invoice", self.invoice.name, "INVOICE", company=self.invoice.company, event_key="manual-invoice:manual-1", coalesce_pending=True)

    def test_native_print_grant_preserves_automatic_event(self):
        printing.queue_invoice_print(self.invoice.name)
        self.assertEqual(self.queue.call_args.kwargs["event_key"], "electronic-invoice")
        self.assertFalse(self.queue.call_args.kwargs["coalesce_pending"])

    def test_print_scoped_grant_keeps_linked_order_context(self):
        self.print_permission.return_value = False
        self.print_fallback.return_value = frappe._dict(can_pay=True)
        printing.queue_invoice_print(self.invoice.name)
        self.print_permission.assert_called_once_with("POS Invoice", "print", self.invoice, print_logs=False)
        self.print_fallback.assert_called_once_with("Order POS", order_owner="waiter@example.invalid")
        self.queue.assert_called_once()

    def test_print_both_denied_never_queues(self):
        self.print_permission.return_value = False
        with self.assertRaises(frappe.PermissionError): printing.queue_invoice_print(self.invoice.name)
        self.queue.assert_not_called()

    def test_print_missing_order_does_not_invent_profile(self):
        self.print_permission.return_value = False
        self.get_value.return_value = None
        with self.assertRaises(frappe.PermissionError): printing.queue_invoice_print(self.invoice.name)
        self.print_fallback.assert_called_once_with(None, order_owner=None)
        self.queue.assert_not_called()

    def test_print_guest_rejected_before_document_access(self):
        with patch.dict(frappe.session, user="Guest"):
            with self.assertRaises(frappe.AuthenticationError): printing.queue_invoice_print(self.invoice.name)
        self.get_doc.assert_not_called()
        self.print_permission.assert_not_called()
        self.queue.assert_not_called()

    def test_invalid_manual_identifier_never_queues(self):
        with self.assertRaises(frappe.ValidationError): printing.queue_invoice_print(self.invoice.name, "<script>")
        self.queue.assert_not_called()

    def test_electronic_native_grant_is_signature_compatible(self):
        electronic_invoice._check_user_access(self.invoice)
        self.electronic_permission.assert_called_once_with("POS Invoice", "write", self.invoice, print_logs=False)
        self.linked_order.assert_not_called()
        self.electronic_fallback.assert_not_called()
        self.queue.assert_not_called()

    def test_electronic_scoped_grant_keeps_linked_order_context(self):
        self.electronic_permission.return_value = False
        self.electronic_fallback.return_value = frappe._dict(can_pay=True)
        electronic_invoice._check_user_access(self.invoice)
        self.electronic_fallback.assert_called_once_with("Order POS", order_owner="waiter@example.invalid")
        self.queue.assert_not_called()

    def test_electronic_without_order_keeps_invoice_context(self):
        self.electronic_permission.return_value = False
        self.linked_order.return_value = None
        self.electronic_fallback.return_value = frappe._dict(can_pay=True)
        electronic_invoice._check_user_access(self.invoice)
        self.electronic_fallback.assert_called_once_with("Test POS", order_owner="owner@example.invalid")

    def test_electronic_both_denied_rejects(self):
        self.electronic_permission.return_value = False
        with self.assertRaises(frappe.PermissionError): electronic_invoice._check_user_access(self.invoice)
        self.queue.assert_not_called()

    def test_electronic_guest_rejected_before_permissions(self):
        with patch.dict(frappe.session, user="Guest"):
            with self.assertRaises(frappe.AuthenticationError): electronic_invoice._check_user_access(self.invoice)
        self.electronic_permission.assert_not_called()
        self.linked_order.assert_not_called()

    def test_print_gate_with_actual_native_permission_callable(self):
        self.assertEqual(frappe.session.user, "Administrator")
        with patch.object(printing, "has_permission", wraps=native_has_permission) as actual:
            printing.queue_invoice_print(self.invoice.name, "actual-native")
        actual.assert_called_once_with("POS Invoice", "print", self.invoice, print_logs=False)
        self.queue.assert_called_once()

    def test_electronic_gate_with_actual_native_permission_callable(self):
        self.assertEqual(frappe.session.user, "Administrator")
        with patch.object(electronic_invoice, "has_permission", wraps=native_has_permission) as actual:
            electronic_invoice._check_user_access(self.invoice)
        actual.assert_called_once_with("POS Invoice", "write", self.invoice, print_logs=False)
        self.queue.assert_not_called()
