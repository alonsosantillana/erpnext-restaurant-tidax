"""Boundary regressions with real Frappe auth/set_user, without a site or database."""

import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import jwt
from werkzeug.wrappers import Request

import frappe
import frappe.auth
from restaurant_management import hooks
from restaurant_management.integrations.pedidosya import api, auth
from restaurant_management.integrations.pedidosya.parsing import PayloadError


DISPATCH = "restaurant_management.integrations.pedidosya.api.dispatch_order"
STATUS = "restaurant_management.integrations.pedidosya.api.update_order_status"
AUTH_HOOK = "restaurant_management.integrations.pedidosya.auth.authenticate_request"


class TestPedidosYaAuthHook(unittest.TestCase):
    def setUp(self):
        self.secret = "isolated-test-only-never-use-as-a-real-jwt-secret-" * 2
        self.settings = SimpleNamespace(
            name="vendor-test", remote_id="vendor-test", enabled=1,
            integration_user="integration@example.test", jwt_algorithm="HS512",
            jwt_issuer=None, jwt_audience=None, jwt_leeway_seconds=0,
            get_password=lambda field: self.secret,
        )
        self.vendors = {self.settings.name: self.settings}
        self.users = {self.settings.integration_user: 1}
        self.overrides = {}
        frappe.local.db = Mock()
        frappe.local.db.get_value.side_effect = self._db_value
        frappe.local.session = frappe._dict(user="Guest", sid=None)
        frappe.local.form_dict = frappe._dict()
        frappe.local.flags = frappe._dict()
        self.patchers = [
            patch("frappe.get_hooks", side_effect=self._get_hooks),
            patch("frappe.get_attr", side_effect=self._get_hook),
            patch("frappe.get_doc", side_effect=self._get_settings),
            patch("frappe.throw", side_effect=self._throw),
            patch.object(auth, "_", side_effect=lambda text: text),
            # Native OAuth/API keys do not recognize an independent middleware JWT.
            patch("frappe.auth.validate_oauth"),
            patch("frappe.auth.validate_auth_via_api_keys"),
            patch("frappe.auth.validate_ip_address"),
            patch("frappe.connect", side_effect=AssertionError("No site connections in this suite")),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(frappe.local.__release_local__)

    @staticmethod
    def _throw(message, exc=frappe.ValidationError, **kwargs):
        raise exc(message)

    def _get_hooks(self, name, default=None, *args, **kwargs):
        if name == "auth_hooks":
            return getattr(hooks, "auth_hooks", [])
        if name == "override_whitelisted_methods":
            return self.overrides
        raise AssertionError(f"Unexpected hook lookup: {name}")

    @staticmethod
    def _get_hook(name):
        if name != AUTH_HOOK:
            raise AssertionError(f"Unexpected authentication hook: {name}")
        return auth.authenticate_request

    def _get_settings(self, doctype, name):
        self.assertEqual(doctype, "PedidosYa Integration Settings")
        return self.vendors[name]

    def _db_value(self, doctype, filters, fieldname, **kwargs):
        if doctype == "PedidosYa Integration Settings":
            self.assertEqual(filters.get("enabled"), 1)
            self.assertIsInstance(filters.get("remote_id"), str)
            vendor = self.vendors.get(filters["remote_id"])
            return vendor.name if vendor and vendor.enabled else None
        if doctype == "User":
            self.assertEqual(fieldname, "enabled")
            return self.users.get(filters)
        raise AssertionError(f"Unexpected database access: {doctype}")

    def _jwt(self, *, secret=None, **overrides):
        claims = {"service": "middleware", "exp": int(time.time()) + 120}
        claims.update(overrides)
        return jwt.encode(claims, secret or self.secret, algorithm="HS512")

    def _request(self, method=DISPATCH, http="POST", token=None, path=None, **values):
        frappe.local.session.user = "Guest"
        frappe.local.form_dict = frappe._dict(remote_id="vendor-test", **values)
        frappe.local.request = Request.from_values(
            path=path or "/api/method/" + method, method=http,
            headers={"Authorization": "Bearer " + (token or self._jwt())},
        )
        frappe.local.response = frappe._dict()

    def _assert_rejected(self):
        with self.assertRaises(frappe.AuthenticationError):
            frappe.auth.validate_auth()
        self.assertEqual(frappe.session.user, "Guest")

    def test_auth_hook_is_registered(self):
        self.assertIn(AUTH_HOOK, getattr(hooks, "auth_hooks", []))

    def test_valid_jwt_crosses_native_auth_and_preserves_form_dict(self):
        self._request(code="TEST", test=True, products=[{"remoteCode": "TEST-ITEM"}])
        original_form = frappe.local.form_dict

        frappe.auth.validate_auth()

        self.assertEqual(frappe.session.user, self.settings.integration_user)
        self.assertIs(frappe.local.form_dict, original_form)
        self.assertTrue(frappe.form_dict.test)
        self.assertEqual(frappe.form_dict.remote_id, "vendor-test")
        frappe.auth.validate_ip_address.assert_called_once_with(self.settings.integration_user)

    def test_dispatch_and_status_exact_routes_and_http_methods(self):
        for prefix in ("/api/method/", "/api/v1/method/"):
            for method, http in ((DISPATCH, "POST"), (STATUS, "POST"), (STATUS, "PUT")):
                with self.subTest(prefix=prefix, method=method, http=http):
                    self._request(method, http, path=prefix + method)
                    frappe.auth.validate_auth()
                    self.assertEqual(frappe.session.user, self.settings.integration_user)

    def test_other_routes_suffixes_and_http_methods_cannot_use_middleware_identity(self):
        paths = ["/api/method/frappe.client.get_list", "/api/resource/User", "/",
                 "/api/method/" + DISPATCH + "/frappe.client.get_list",
                 "/api/method/" + DISPATCH + ".other", "/api/method/" + DISPATCH + "/"]
        for path in paths:
            with self.subTest(path=path):
                self._request(path=path)
                self._assert_rejected()
        for http in ("GET", "DELETE", "PATCH", "OPTIONS", "PUT"):
            with self.subTest(http=http):
                self._request(http=http)
                self._assert_rejected()

    def test_cmd_and_effective_override_cannot_redirect_identity(self):
        for cmd in ("frappe.client.get_list", STATUS, [DISPATCH]):
            with self.subTest(cmd=cmd):
                self._request(cmd=cmd)
                self._assert_rejected()
        self.overrides = {DISPATCH: ["frappe.client.get_list"]}
        self._request()
        self._assert_rejected()

    def test_same_cmd_does_not_change_dispatch_target(self):
        self._request(cmd=DISPATCH)
        frappe.auth.validate_auth()
        self.assertEqual(frappe.form_dict.cmd, DISPATCH)

    def test_missing_malformed_or_invalid_jwt_never_grants_identity(self):
        headers = [None, "", "Basic dummy", "Bearer invalid",
                   "Bearer " + self._jwt(secret=self.secret + "wrong"),
                   "Bearer " + self._jwt(exp=int(time.time()) - 60),
                   "Bearer " + self._jwt(service="other")]
        for header in headers:
            with self.subTest(header_kind=(header or "missing").split(" ")[0]):
                self._request()
                frappe.local.request = Request.from_values(
                    path="/api/method/" + DISPATCH, method="POST",
                    headers={"Authorization": header} if header else {},
                )
                self._assert_rejected()

    def test_missing_exp_is_rejected_and_zero_leeway_is_honored(self):
        no_exp = jwt.encode({"service": "middleware"}, self.secret, algorithm="HS512")
        self._request(token=no_exp)
        self._assert_rejected()
        self._request(token=self._jwt(exp=int(time.time()) - 5))
        self._assert_rejected()

    def test_service_claim_is_required_even_with_valid_expiration(self):
        token = jwt.encode({"exp": int(time.time()) + 60}, self.secret, algorithm="HS512")
        self._request(token=token)
        self._assert_rejected()

    def test_all_allowed_hmac_algorithms_and_default_leeway(self):
        for algorithm in ("HS256", "HS384", "HS512"):
            with self.subTest(algorithm=algorithm):
                self.settings.jwt_algorithm = algorithm
                token = jwt.encode({"service": "middleware", "exp": int(time.time()) + 60},
                                   self.secret, algorithm=algorithm)
                self._request(token=token)
                frappe.auth.validate_auth()
                self.assertEqual(frappe.session.user, self.settings.integration_user)
        self.settings.jwt_leeway_seconds = None
        self._request(token=self._jwt(exp=int(time.time()) - 5))
        frappe.auth.validate_auth()
        self.assertEqual(frappe.session.user, self.settings.integration_user)

    def test_issuer_audience_and_algorithm_are_enforced(self):
        for field, claim in (("jwt_issuer", "iss"), ("jwt_audience", "aud")):
            with self.subTest(field=field):
                setattr(self.settings, field, "expected")
                self._request(token=self._jwt(**{claim: "wrong"}))
                self._assert_rejected()
                self._request(token=self._jwt(**{claim: "expected"}))
                frappe.auth.validate_auth()
                self.assertEqual(frappe.session.user, self.settings.integration_user)
                setattr(self.settings, field, None)
        self.settings.jwt_algorithm = "HS256"
        self._request()
        self._assert_rejected()
        self.settings.jwt_algorithm = "none"
        self._request()
        self._assert_rejected()

    def test_disabled_vendor_or_bad_remote_id_cannot_authenticate(self):
        self.settings.enabled = 0
        self._request()
        self._assert_rejected()
        self.settings.enabled = 1
        for remote_id in (None, "", [], {"operator": "!="}, "missing-vendor"):
            with self.subTest(remote_id=remote_id):
                self._request()
                frappe.form_dict.remote_id = remote_id
                self._assert_rejected()

    def test_disabled_missing_and_special_integration_users_are_rejected(self):
        for user, enabled in (("missing@example.test", None), ("disabled@example.test", 0),
                              ("Guest", 1), ("Administrator", 1), (None, 1)):
            with self.subTest(user=user):
                self.settings.integration_user = user
                self.users[user] = enabled
                self._request()
                self._assert_rejected()

    def test_token_for_other_vendor_is_rejected(self):
        other = SimpleNamespace(**vars(self.settings))
        other.name = other.remote_id = "other-vendor"
        other.get_password = lambda field: self.secret + "-other"
        self.vendors[other.name] = other
        self._request()
        frappe.form_dict.remote_id = other.remote_id
        self._assert_rejected()

    def test_existing_admin_session_does_not_skip_jwt_validation(self):
        self._request(token="invalid")
        frappe.local.session.user = "admin@example.test"
        with self.assertRaises(frappe.AuthenticationError):
            frappe.auth.validate_auth()
        self.assertEqual(frappe.session.user, "admin@example.test")

    def test_unrelated_native_request_is_untouched(self):
        self._request(path="/api/method/frappe.client.get_list")
        frappe.local.session.user = "native-api-user@example.test"
        frappe.auth.validate_auth()
        self.assertEqual(frappe.session.user, "native-api-user@example.test")
        frappe.get_doc.assert_not_called()

    def test_missing_request_context_is_a_noop(self):
        frappe.local.request = None
        hook = getattr(auth, "authenticate_request", None)
        self.assertIsNotNone(hook)
        hook()
        self.assertEqual(frappe.session.user, "Guest")
        frappe.get_doc.assert_not_called()

    @patch.object(api, "receive_order")
    def test_authenticated_dispatch_retains_202_200_contract(self, receive_order):
        receive_order.side_effect = [({"remoteOrderId": "PYA-TEST"}, True),
                                     ({"remoteOrderId": "PYA-TEST"}, False)]
        payload = {"test": True, "token": "test-token", "code": "TEST-ONLY"}
        for expected_status in (202, 200):
            self._request()
            frappe.local.request = Request.from_values(
                path="/api/method/" + DISPATCH, method="POST", json=payload,
                headers={"Authorization": "Bearer " + self._jwt()},
            )
            frappe.auth.validate_auth()
            api.dispatch_order(**frappe.form_dict)
            self.assertEqual(frappe.local.response.http_status_code, expected_status)
            self.assertEqual(frappe.local.response.remoteResponse, {"remoteOrderId": "PYA-TEST"})
            self.assertEqual(receive_order.call_args.args, (self.settings, payload))

    @patch.object(api, "receive_status")
    def test_authenticated_status_preserves_remote_order_and_200_contract(self, receive_status):
        payload = {"status": "ORDER_CANCELLED"}
        self._request(STATUS, "PUT", remote_order_id="PYA-TEST")
        frappe.local.request = Request.from_values(
            path="/api/method/" + STATUS, method="PUT", json=payload,
            headers={"Authorization": "Bearer " + self._jwt()},
        )
        frappe.auth.validate_auth()
        api.update_order_status(**frappe.form_dict)
        self.assertEqual(frappe.local.response.http_status_code, 200)
        receive_status.assert_called_once_with(self.settings, "PYA-TEST", payload)

    @patch.object(api, "receive_order", side_effect=PayloadError("Invalid test payload"))
    def test_authenticated_invalid_payload_retains_400_contract(self, receive_order):
        self._request()
        frappe.auth.validate_auth()
        api.dispatch_order(**frappe.form_dict)
        self.assertEqual(frappe.local.response.http_status_code, 400)
        self.assertEqual(frappe.local.response.reason, "INVALID_REQUEST")

    def test_user_switch_clears_previous_permission_cache(self):
        self._request()
        frappe.local.session.user = "admin@example.test"
        frappe.local.role_permissions = {"admin-only": True}
        frappe.auth.validate_auth()
        self.assertEqual(frappe.session.user, self.settings.integration_user)
        self.assertEqual(frappe.local.role_permissions, {})


if __name__ == "__main__":
    unittest.main()
