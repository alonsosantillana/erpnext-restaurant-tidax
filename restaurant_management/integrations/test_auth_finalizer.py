"""Offline bridge regressions using Frappe's native authentication runner."""

import builtins
import importlib
import unittest
from unittest.mock import Mock, call, patch

from werkzeug.wrappers import Request

import frappe
import frappe.auth
from frappe.utils.local import release_local
from restaurant_management import hooks
from restaurant_management.integrations import auth_finalizer


AUTH_HOOK = "restaurant_management.integrations.pedidosya.auth.authenticate_request"
FINALIZER_HOOK = "restaurant_management.integrations.auth_finalizer.authenticate_request"
CALLBACK_HOOK = "tix_mcp_read_auth_finalizers"
FIRST = "synthetic_app.finalizers.first"
SECOND = "synthetic_app.finalizers.second"


class TestAuthFinalizer(unittest.TestCase):
    def setUp(self):
        self.addCleanup(release_local, frappe.local)
        release_local(frappe.local)
        frappe.local.db = Mock(spec=[])
        frappe.local.session = frappe._dict(user="Guest", sid=None)
        frappe.local.form_dict = frappe._dict()
        frappe.local.flags = frappe._dict()
        frappe.local.request = Request.from_values(path="/unrelated", method="GET")
        self.callbacks = []
        self.pedidosya = Mock(name="pedidosya_authenticator")
        self.first = Mock(name="first_finalizer")
        self.second = Mock(name="second_finalizer")
        self.dispatch = Mock(name="business_dispatch")
        self.callback_methods = {FIRST: self.first, SECOND: self.second}
        self.get_hooks = self.enterContext(patch("frappe.get_hooks", side_effect=self._get_hooks))
        self.get_attr = self.enterContext(patch("frappe.get_attr", side_effect=self._get_attr))
        self.enterContext(patch("frappe.throw", side_effect=self._throw))
        self.enterContext(patch("frappe.auth.validate_oauth"))
        self.enterContext(patch("frappe.auth.validate_auth_via_api_keys"))
        self.ip_check = self.enterContext(patch("frappe.auth.validate_ip_address"))
        for target in (
            "socket.socket.connect", "frappe.init", "frappe.connect", "frappe.get_doc",
            "frappe.get_all", "frappe.enqueue", "frappe.sendmail", "frappe.publish_realtime",
        ):
            self.enterContext(patch(target, side_effect=AssertionError("Real IO is forbidden")))

    @staticmethod
    def _throw(message, exc=frappe.ValidationError, **kwargs):
        raise exc(message)

    def _get_hooks(self, name, default=None, *args, **kwargs):
        if name == "auth_hooks":
            return hooks.auth_hooks
        if name == CALLBACK_HOOK:
            return self.callbacks
        raise AssertionError(f"Unexpected hook lookup: {name}")

    def _get_attr(self, name):
        if name == AUTH_HOOK:
            return self.pedidosya
        if name == FINALIZER_HOOK:
            return auth_finalizer.authenticate_request
        return self.callback_methods[name]

    def _dispatch_after_native_auth(self):
        frappe.auth.validate_auth()
        self.dispatch()

    def test_bridge_is_registered_once_immediately_after_pedidosya(self):
        self.assertEqual(hooks.auth_hooks.count(AUTH_HOOK), 1)
        self.assertEqual(hooks.auth_hooks.count(FINALIZER_HOOK), 1)
        self.assertEqual(hooks.auth_hooks.index(FINALIZER_HOOK), hooks.auth_hooks.index(AUTH_HOOK) + 1)

    def test_missing_callbacks_use_empty_default_without_resolving_a_callable(self):
        self.get_hooks.side_effect = lambda name, default=None: default
        self.assertIsNone(auth_finalizer.authenticate_request())
        self.get_hooks.assert_called_once_with(CALLBACK_HOOK, default=[])
        self.get_attr.assert_not_called()

    def test_empty_callbacks_do_not_change_identity_or_request(self):
        session = dict(frappe.session)
        form = frappe.local.form_dict
        request = frappe.local.request
        self.assertIsNone(auth_finalizer.authenticate_request())
        self.assertEqual(dict(frappe.session), session)
        self.assertIs(frappe.local.form_dict, form)
        self.assertIs(frappe.local.request, request)
        self.get_attr.assert_not_called()

    def test_no_request_context_and_no_callbacks_is_a_noop(self):
        frappe.local.request = None
        auth_finalizer.authenticate_request()
        self.get_attr.assert_not_called()
        self.assertEqual(frappe.session.user, "Guest")

    def test_empty_tuple_is_a_noop(self):
        self.callbacks = ()
        self.assertIsNone(auth_finalizer.authenticate_request())
        self.get_attr.assert_not_called()
        self.assertEqual(frappe.session.user, "Guest")

    def test_tuple_callbacks_resolve_and_execute_once_in_order(self):
        self.callbacks = (FIRST, SECOND)
        original = self.callbacks
        events = []
        self.first.side_effect = lambda: events.append("first")
        self.second.side_effect = lambda: events.append("second")
        auth_finalizer.authenticate_request()
        self.assertEqual(events, ["first", "second"])
        self.assertIs(self.callbacks, original)
        self.assertEqual(self.get_attr.call_args_list, [call(FIRST), call(SECOND)])
        self.first.assert_called_once_with()
        self.second.assert_called_once_with()

    def test_callbacks_resolve_and_execute_once_in_order_without_mutating_list(self):
        self.callbacks = [FIRST, SECOND]
        original = list(self.callbacks)
        events = []
        self.first.side_effect = lambda: events.append("first")
        self.second.side_effect = lambda: events.append("second")
        auth_finalizer.authenticate_request()
        self.assertEqual(events, ["first", "second"])
        self.assertEqual(self.callbacks, original)
        self.assertEqual(self.get_attr.call_args_list, [call(FIRST), call(SECOND)])
        self.first.assert_called_once_with()
        self.second.assert_called_once_with()

    def test_callback_list_is_snapshotted_before_callback_execution(self):
        self.callbacks = [FIRST, SECOND]
        self.first.side_effect = self.callbacks.clear
        auth_finalizer.authenticate_request()
        self.first.assert_called_once_with()
        self.second.assert_called_once_with()

    def test_malformed_callback_lists_deny_before_any_resolution(self):
        invalid = (
            None, False, "", FIRST, {FIRST}, {"callback": FIRST},
            [None], [False], [1], [self.first], [[]], [""], ["single_name"],
            [".module.method"], ["module..method"], ["module.method."],
            [" module.method"], ["module.method "], ["module.method()"],
            ["module.method/other"], ["module.1method"], [FIRST, None], (FIRST, None),
            (FIRST, FIRST),
        )
        for callbacks in invalid:
            with self.subTest(callbacks=repr(callbacks)):
                self.callbacks = callbacks
                with self.assertRaises(frappe.PermissionError):
                    auth_finalizer.authenticate_request()
                self.get_attr.assert_not_called()
                self.first.assert_not_called()

    def test_duplicate_callbacks_deny_before_any_resolution_without_mutation(self):
        self.callbacks = [FIRST, SECOND, FIRST]
        original = list(self.callbacks)
        with self.assertRaises(frappe.PermissionError):
            auth_finalizer.authenticate_request()
        self.assertEqual(self.callbacks, original)
        self.get_attr.assert_not_called()

    def test_hook_lookup_errors_propagate(self):
        error = RuntimeError("synthetic hook lookup failure")
        self.get_hooks.side_effect = error
        with self.assertRaises(RuntimeError) as raised:
            auth_finalizer.authenticate_request()
        self.assertIs(raised.exception, error)
        self.get_attr.assert_not_called()

    def test_callback_resolution_errors_propagate(self):
        self.callbacks = [FIRST]
        error = ImportError("synthetic callback resolution failure")
        self.get_attr.side_effect = error
        with self.assertRaises(ImportError) as raised:
            auth_finalizer.authenticate_request()
        self.assertIs(raised.exception, error)
        self.first.assert_not_called()

    def test_callback_exceptions_propagate_and_stop_later_callbacks(self):
        self.callbacks = [FIRST, SECOND]
        for error in (frappe.PermissionError("denied"), frappe.AuthenticationError(), RuntimeError("failed")):
            with self.subTest(error=type(error).__name__):
                self.first.reset_mock()
                self.get_attr.reset_mock()
                self.first.side_effect = error
                with self.assertRaises(type(error)) as raised:
                    auth_finalizer.authenticate_request()
                self.assertIs(raised.exception, error)
                self.first.assert_called_once_with()
                self.second.assert_not_called()
                self.get_attr.assert_called_once_with(FIRST)

    def test_callback_return_values_do_not_replace_native_authentication(self):
        self.callbacks = [FIRST, SECOND]
        self.first.return_value = False
        self.second.return_value = True
        self.assertIsNone(auth_finalizer.authenticate_request())
        self.second.assert_called_once_with()

    def test_native_runner_runs_bridge_after_authenticator_on_unrelated_route(self):
        self.callbacks = [FIRST]
        events = []

        def select_user():
            events.append("pedidosya")
            frappe.set_user("synthetic-api@example.test")

        self.pedidosya.side_effect = select_user
        self.first.side_effect = lambda: events.append(frappe.session.user)
        self.dispatch.side_effect = lambda: events.append("dispatch")
        self._dispatch_after_native_auth()
        self.assertEqual(events, ["pedidosya", "synthetic-api@example.test", "dispatch"])
        self.ip_check.assert_called_once_with("synthetic-api@example.test")

    def test_native_runner_preserves_standalone_guest_with_empty_callbacks(self):
        self._dispatch_after_native_auth()
        self.assertEqual(frappe.session.user, "Guest")
        self.pedidosya.assert_called_once_with()
        self.dispatch.assert_called_once_with()
        self.ip_check.assert_not_called()

    def test_native_runner_does_not_finalize_or_dispatch_after_authenticator_failure(self):
        self.callbacks = [FIRST]
        error = frappe.AuthenticationError("synthetic JWT rejection")
        self.pedidosya.side_effect = error
        with self.assertRaises(frappe.AuthenticationError) as raised:
            self._dispatch_after_native_auth()
        self.assertIs(raised.exception, error)
        self.get_attr.assert_called_once_with(AUTH_HOOK)
        self.first.assert_not_called()
        self.dispatch.assert_not_called()

    def test_native_runner_aborts_dispatch_after_finalizer_denial(self):
        self.callbacks = [FIRST, SECOND]
        self.pedidosya.side_effect = lambda: frappe.set_user("synthetic-api@example.test")
        error = frappe.PermissionError("synthetic finalizer denial")
        self.first.side_effect = error
        with self.assertRaises(frappe.PermissionError) as raised:
            self._dispatch_after_native_auth()
        self.assertIs(raised.exception, error)
        self.second.assert_not_called()
        self.dispatch.assert_not_called()
        self.ip_check.assert_not_called()

    def test_native_guest_guard_still_rejects_unauthenticated_bearer(self):
        self.callbacks = [FIRST]
        frappe.local.request = Request.from_values(headers={"Authorization": "Bearer synthetic"})
        with self.assertRaises(frappe.AuthenticationError):
            self._dispatch_after_native_auth()
        self.first.assert_called_once_with()
        self.assertEqual(frappe.session.user, "Guest")
        self.dispatch.assert_not_called()

    def test_native_ip_denial_still_aborts_after_finalizer(self):
        self.callbacks = [FIRST]
        self.pedidosya.side_effect = lambda: frappe.set_user("synthetic-api@example.test")
        self.ip_check.side_effect = frappe.AuthenticationError("synthetic IP rejection")
        with self.assertRaises(frappe.AuthenticationError):
            self._dispatch_after_native_auth()
        self.first.assert_called_once_with()
        self.dispatch.assert_not_called()

    def test_bridge_import_does_not_require_tix_and_is_not_a_public_api(self):
        original_import = builtins.__import__

        def without_tix(name, *args, **kwargs):
            if name == "tix" or name.startswith("tix."):
                raise AssertionError("Restaurant must not import TIX")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=without_tix):
            importlib.reload(auth_finalizer)
            auth_finalizer.authenticate_request()
        self.assertNotIn("tix", hooks.required_apps)
        self.assertNotIn(auth_finalizer.authenticate_request, frappe.whitelisted)
        self.assertNotIn(auth_finalizer.authenticate_request, frappe.guest_methods)


if __name__ == "__main__":
    unittest.main()
