"""Callback regression tests with the installed Frappe enqueue; no Redis/DB/HTTP I/O."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe
from frappe.utils import background_jobs as bg
from restaurant_management.integrations.pedidosya import service

FQN = "restaurant_management.integrations.pedidosya.service.send_callback"
EVENTS = ("accepted", "rejected", "prepared", "picked_up")


class AfterCommit:
    def __init__(self):
        self.items = []

    def add(self, callback):
        self.items.append(callback)

    def run(self):
        items, self.items = self.items, []
        for callback in items:
            callback()


class CapturedQueue:
    def __init__(self):
        self.calls = []

    def enqueue_call(self, *args, **kwargs):
        self.calls.append(kwargs)
        return kwargs


class CallbackDoc(SimpleNamespace):
    def db_set(self, values):
        self.updates.append(values)
        self.__dict__.update(values)

    def check_permission(self, permission):
        assert permission == "write"


class TestCallbackQueue(unittest.TestCase):
    def setUp(self):
        frappe.local.flags = frappe._dict(in_test=False)
        self.addCleanup(frappe.local.__release_local__)
        self.after = AfterCommit()
        self.queue = CapturedQueue()
        self.doc = CallbackDoc(
            name="TDX-TEST-CALLBACK", settings="TDX-TEST-SETTINGS", status="Imported",
            table_order="TDX-TEST-ORDER", fulfillment=None, updates=[],
            rejection_reason="ITEM_UNAVAILABLE", rejection_message="Synthetic rejection",
            **{event + "_callback_url": "https://callbacks.example.com/" + event for event in EVENTS},
            **{event + "_notified": 0 for event in EVENTS},
        )
        self.settings = SimpleNamespace(
            name=self.doc.settings, integration_flow="Direct", default_preparation_minutes=20
        )
        self.db = Mock()
        self.db.after_commit = self.after
        self.fake = SimpleNamespace(
            conf={}, local=SimpleNamespace(site="v15.local"),
            session=SimpleNamespace(user="Administrator"), flags=SimpleNamespace(in_test=False),
            db=self.db, enqueue=bg.enqueue, get_doc=Mock(side_effect=self.get_doc), get_all=Mock(),
        )
        self.http = Mock()
        for context in [
            patch.object(service, "frappe", self.fake),
            patch.object(bg, "frappe", self.fake),
            patch.object(bg, "get_job", return_value=None),
            patch.object(bg, "get_queue", return_value=self.queue),
            patch.object(bg, "_check_queue_size", return_value=None),
            patch.object(bg, "get_queues_timeout", return_value={"short": 300}),
            patch.object(service, "post_callback", self.http),
            patch.object(service, "now_datetime", return_value="2026-10-27 12:00:00"),
        ]:
            context.start()
            self.addCleanup(context.stop)

    def get_doc(self, doctype, name):
        if doctype == "PedidosYa Order":
            self.assertEqual(name, self.doc.name)
            return self.doc
        if doctype == "PedidosYa Integration Settings":
            self.assertEqual(name, self.doc.settings)
            return self.settings
        if doctype == "Table Order":
            return SimpleNamespace(send=None)
        self.fail("Unexpected document access: " + doctype)

    def assert_payload(self, event):
        self.http.assert_called_once()
        settings, url, payload = self.http.call_args.args
        self.assertIs(settings, self.settings)
        self.assertEqual(url, getattr(self.doc, event + "_callback_url"))
        if event == "prepared":
            self.assertIsNone(payload)
        elif event == "accepted":
            self.assertEqual(payload["status"], "order_accepted")
            self.assertEqual(payload["remoteOrderId"], self.doc.name)
            self.assertIn("acceptanceTime", payload)
        elif event == "rejected":
            self.assertEqual(payload, {
                "status": "order_rejected", "reason": self.doc.rejection_reason,
                "message": self.doc.rejection_message,
            })
        else:
            self.assertEqual(payload, {"status": "order_picked_up"})
        self.assertEqual(getattr(self.doc, event + "_notified"), 1)

    def assert_queued_callback(self, event, expected_job_id):
        self.assertEqual(self.queue.calls, [], "Callback must wait until commit")
        self.after.run()
        self.assertEqual(len(self.queue.calls), 1)
        call = self.queue.calls[0]
        self.assertEqual(call["job_id"], bg.create_job_id(expected_job_id))
        self.assertIsNone(call["kwargs"]["event"], "Reserved Frappe event must remain empty")
        args = call["kwargs"]["kwargs"]
        self.assertEqual(args["callback_event"], event)
        self.assertNotIn("event", args)
        service.send_callback(**args)
        self.assert_payload(event)

    def test_reserved_event_collision_is_reproduced_by_installed_enqueue(self):
        service._queue(FQN, name=self.doc.name, event="accepted", job_id="TDX-TEST-OLD")
        self.after.run()
        transport = self.queue.calls[0]["kwargs"]
        self.assertEqual(transport["event"], "accepted")
        self.assertEqual(transport["kwargs"], {"name": self.doc.name})

    def test_accept_producer_preserves_event_after_commit(self):
        service._accept(self.doc.name, automatic=True)
        self.assert_queued_callback("accepted", "pedidosya-accepted:" + self.doc.name)

    def test_reject_producer_preserves_event_and_reason(self):
        self.doc.status = "Awaiting Acceptance"
        service.reject_order(self.doc.name, "ITEM_UNAVAILABLE", self.doc.rejection_message)
        self.assert_queued_callback("rejected", "pedidosya-rejected:" + self.doc.name)

    def test_prepared_producer_preserves_empty_body(self):
        self.db.get_value.side_effect = [
            self.doc.name, SimpleNamespace(fulfillment_type="Delivery", delivery_provider="PedidosYa")
        ]
        service.notify_prepared_by_fulfillment("TDX-TEST-FULFILLMENT")
        self.assert_queued_callback("prepared", "pedidosya-prepared:" + self.doc.name)

    def test_pickup_producer_preserves_event(self):
        self.db.get_value.side_effect = [
            self.doc.name, SimpleNamespace(fulfillment_type="Pickup", delivery_provider="Restaurant")
        ]
        service.notify_picked_up_by_fulfillment("TDX-TEST-FULFILLMENT")
        self.assert_queued_callback("picked_up", "pedidosya-picked-up:" + self.doc.name)

    def test_recovery_producer_preserves_both_events(self):
        for event, status in [("accepted", "Accepted"), ("rejected", "Rejected")]:
            with self.subTest(event=event):
                self.queue.calls.clear()
                self.doc.status = status
                setattr(self.doc, event + "_notified", 0)
                self.http.reset_mock()
                self.fake.get_all.side_effect = [[], [], [self.doc], [], []]
                self.db.get_value.side_effect = None
                self.db.get_value.return_value = "Direct"
                service.recover_pending_orders()
                self.assert_queued_callback(event, "pedidosya-" + event + "-recovery:" + self.doc.name)

    def test_all_events_support_queued_named_and_positional_calls(self):
        for event in EVENTS:
            for style in ("callback_event", "event", "positional", "same_alias"):
                with self.subTest(event=event, style=style):
                    setattr(self.doc, event + "_notified", 0)
                    self.http.reset_mock()
                    if style == "positional":
                        service.send_callback(self.doc.name, event)
                    elif style == "same_alias":
                        service.send_callback(self.doc.name, event=event, callback_event=event)
                    else:
                        service.send_callback(self.doc.name, **{style: event})
                    self.assert_payload(event)

    def test_missing_invalid_and_conflicting_events_fail_before_access(self):
        self.fake.get_doc.reset_mock()
        for kwargs in (
            {}, {"event": "invalid"}, {"callback_event": "invalid"},
            {"event": "accepted", "callback_event": "rejected"},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    service.send_callback(self.doc.name, **kwargs)
        self.fake.get_doc.assert_not_called()
        self.http.assert_not_called()

    def test_http_failure_does_not_confirm_notification(self):
        self.http.side_effect = RuntimeError("Synthetic HTTP failure")
        with self.assertRaisesRegex(RuntimeError, "Synthetic"):
            service.send_callback(self.doc.name, callback_event="prepared")
        self.assertEqual(self.doc.prepared_notified, 0)
        self.assertEqual(self.doc.updates, [])

    def test_absent_url_does_not_send_or_confirm(self):
        self.doc.prepared_callback_url = None
        service.send_callback(self.doc.name, callback_event="prepared")
        self.http.assert_not_called()
        self.assertEqual(self.doc.prepared_notified, 0)
