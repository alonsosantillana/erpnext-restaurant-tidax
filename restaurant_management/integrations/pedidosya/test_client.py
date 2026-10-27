"""Outbound auth regressions; installed RedisWrapper with all network I/O mocked."""
import json
import pickle
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe
import requests
from frappe.utils.redis_wrapper import RedisWrapper
from restaurant_management.integrations.pedidosya import client, service


def response(status=204, data=None):
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(data).encode() if data is not None else b""
    return result


class TestCallbackTokenRefresh(unittest.TestCase):
    def setUp(self):
        frappe.local.conf = frappe._dict(db_name="unit_callback_site")
        frappe.local.cache = {}
        self.addCleanup(frappe.local.__release_local__)
        self.cache = RedisWrapper()
        self.remote = {}
        self.settings = SimpleNamespace(
            name="TDX-TEST-AUTH", api_base_url="https://callbacks.example.test",
            callback_allowed_hosts="", api_username="synthetic",
            get_password=Mock(return_value="synthetic-password"), default_preparation_minutes=20,
        )
        self.key = "pedidosya:access-token:" + self.settings.name
        self.raw_key = self.cache.make_key(self.key)
        self.url = self.settings.api_base_url + "/mock/orders/TDX-TEST-AUTH/prepared"
        self.login = self.settings.api_base_url + "/v2/login"
        self.concurrent_token = None
        self.eval_results = []
        self.set_token("rejected-token")
        self.post = Mock()
        self.eval = Mock(side_effect=self.compare_delete)
        for context in (
            patch.object(self.cache, "get", side_effect=self.remote.get),
            patch.object(self.cache, "setex", side_effect=self.setex),
            patch.object(self.cache, "eval", self.eval),
            patch.object(client, "frappe", SimpleNamespace(cache=self.cache, local=frappe.local)),
            patch.object(client.requests, "post", self.post),
        ):
            context.start()
            self.addCleanup(context.stop)

    def set_token(self, value):
        self.remote[self.raw_key] = pickle.dumps(value)

    def setex(self, name, time, value):
        self.assertGreater(time, 0)
        self.remote[name] = value

    def compare_delete(self, script, numkeys, key, expected):
        self.assertEqual(numkeys, 1)
        self.assertEqual(key, self.raw_key)
        self.assertIn("redis.call", script)
        if self.concurrent_token:
            self.set_token(self.concurrent_token)
        matched = self.remote.get(key) == expected
        if matched:
            del self.remote[key]
        self.eval_results.append(int(matched))
        return int(matched)

    def fresh_login(self):
        return response(200, {"access_token": "fresh-token", "expires_in": 3600})

    def assert_requests(self, urls):
        self.assertEqual([call.args[0] for call in self.post.call_args_list], urls)
        for call in self.post.call_args_list:
            self.assertEqual(call.kwargs["timeout"], client.TIMEOUT)
            self.assertNotIn("verify", call.kwargs)

    def test_cached_token_success_has_no_login_or_invalidation(self):
        self.post.return_value = response(204)
        self.assertEqual(client.post_callback(self.settings, self.url), {})
        self.assert_requests([self.url])
        self.eval.assert_not_called()

    def test_empty_cache_logs_in_once(self):
        self.remote.clear()
        self.post.side_effect = [self.fresh_login(), response(204)]
        client.post_callback(self.settings, self.url)
        self.assert_requests([self.login, self.url])
        self.assertEqual(self.post.call_args_list[0].kwargs["data"], {
            "grant_type": "client_credentials", "username": "synthetic", "password": "synthetic-password",
        })
        self.eval.assert_not_called()

    def test_401_renews_once_and_preserves_prepared_empty_body(self):
        self.post.side_effect = [response(401), self.fresh_login(), response(204)]
        self.assertEqual(client.post_callback(self.settings, self.url), {})
        self.assert_requests([self.url, self.login, self.url])
        self.assertEqual(self.eval_results, [1])
        calls = (self.post.call_args_list[0], self.post.call_args_list[2])
        self.assertEqual([c.kwargs["headers"]["Authorization"] for c in calls],
                         ["Bearer rejected-token", "Bearer fresh-token"])
        self.assertTrue(all("json" not in c.kwargs and "data" not in c.kwargs for c in calls))
        self.assertEqual(pickle.loads(self.remote[self.raw_key]), "fresh-token")

    def test_payload_and_success_response_preserved(self):
        for payload in ({"status": "order_accepted", "remoteOrderId": "TDX-TEST"},
                        {"status": "order_rejected", "reason": "ITEM_UNAVAILABLE"},
                        {"status": "order_picked_up"}):
            with self.subTest(payload=payload):
                self.set_token("rejected-token")
                self.post.reset_mock()
                self.post.side_effect = [response(401), self.fresh_login(), response(200, {"ok": True})]
                self.assertEqual(client.post_callback(self.settings, self.url, payload), {"ok": True})
                for index in (0, 2):
                    self.assertEqual(self.post.call_args_list[index].kwargs["json"], payload)

    def test_second_401_is_not_retried(self):
        self.post.side_effect = [response(401), self.fresh_login(), response(401)]
        with self.assertRaises(requests.HTTPError):
            client.post_callback(self.settings, self.url)
        self.assert_requests([self.url, self.login, self.url])
        self.assertEqual(self.eval.call_count, 1)

    def test_cold_cache_first_401_has_at_most_two_logins(self):
        self.remote.clear()
        self.post.side_effect = [self.fresh_login(), response(401), self.fresh_login(), response(401)]
        with self.assertRaises(requests.HTTPError):
            client.post_callback(self.settings, self.url)
        self.assert_requests([self.login, self.url, self.login, self.url])
        self.assertEqual(self.eval.call_count, 1)

    def test_login_failures_do_not_replay_callback(self):
        for failure in (response(401), response(500), response(200, {}),
                        requests.Timeout("synthetic"), requests.ConnectionError("synthetic")):
            with self.subTest(failure=type(failure).__name__):
                self.set_token("rejected-token")
                self.post.reset_mock()
                self.post.side_effect = [response(401), failure]
                with self.assertRaises((requests.RequestException, ValueError)):
                    client.post_callback(self.settings, self.url)
                self.assert_requests([self.url, self.login])

    def test_initial_login_401_does_not_enter_callback_retry(self):
        self.remote.clear()
        self.post.return_value = response(401)
        with self.assertRaises(requests.HTTPError):
            client.post_callback(self.settings, self.url)
        self.assert_requests([self.login])
        self.eval.assert_not_called()

    def test_other_callback_errors_do_not_invalidate_or_retry(self):
        for failure in (response(403), response(429), response(500), response(503),
                        requests.Timeout("synthetic"), requests.ConnectionError("synthetic")):
            with self.subTest(failure=type(failure).__name__):
                self.post.reset_mock()
                self.post.side_effect = [failure]
                with self.assertRaises(requests.RequestException):
                    client.post_callback(self.settings, self.url)
                self.assert_requests([self.url])
                self.eval.assert_not_called()
                self.assertEqual(pickle.loads(self.remote[self.raw_key]), "rejected-token")

    def test_new_token_published_during_invalidation_is_preserved(self):
        self.concurrent_token = "concurrently-renewed-token"
        self.post.side_effect = [response(401), response(204)]
        client.post_callback(self.settings, self.url)
        self.assert_requests([self.url, self.url])
        self.assertEqual(self.eval_results, [0])
        self.assertEqual(pickle.loads(self.remote[self.raw_key]), self.concurrent_token)
        self.assertEqual(self.post.call_args.kwargs["headers"]["Authorization"],
                         "Bearer " + self.concurrent_token)

    def test_absent_remote_token_during_invalidation_logs_in(self):
        def first_request(*args, **kwargs):
            self.remote.pop(self.raw_key)
            self.post.side_effect = [self.fresh_login(), response(204)]
            return response(401)
        self.post.side_effect = first_request
        client.post_callback(self.settings, self.url)
        self.assertEqual(self.eval_results, [0])
        self.assert_requests([self.url, self.login, self.url])

    def test_stale_local_copy_is_discarded_without_touching_other_keys(self):
        frappe.local.cache[self.raw_key] = "obsolete-local-token"
        other_key = self.cache.make_key("pedidosya:access-token:TDX-TEST-OTHER")
        other_site_key = b"another_site|" + self.key.encode()
        self.remote[other_key] = pickle.dumps("other-integration")
        self.remote[other_site_key] = pickle.dumps("other-site")
        frappe.local.cache[other_key] = "other-local"
        self.post.side_effect = [response(401), self.fresh_login(), response(204)]
        client.post_callback(self.settings, self.url)
        self.assertEqual(self.post.call_args_list[0].kwargs["headers"]["Authorization"],
                         "Bearer rejected-token")
        self.assertNotIn(self.raw_key, frappe.local.cache)
        self.assertEqual(frappe.local.cache[other_key], "other-local")
        self.assertEqual(pickle.loads(self.remote[other_key]), "other-integration")
        self.assertEqual(pickle.loads(self.remote[other_site_key]), "other-site")

    def test_expired_remote_token_not_replaced_by_stale_local_copy(self):
        frappe.local.cache[self.raw_key] = "expired-local-token"
        self.remote.clear()
        self.post.side_effect = [self.fresh_login(), response(204)]
        client.post_callback(self.settings, self.url)
        self.assert_requests([self.login, self.url])
        self.assertNotIn(self.raw_key, frappe.local.cache)

    def test_cache_invalidation_failure_does_not_replay(self):
        self.eval.side_effect = RuntimeError("synthetic Redis failure")
        self.post.return_value = response(401)
        with self.assertRaisesRegex(RuntimeError, "synthetic"):
            client.post_callback(self.settings, self.url)
        self.assert_requests([self.url])

    def test_invalid_destination_fails_before_authentication(self):
        self.remote.clear()
        with patch.object(client, "_", side_effect=lambda text: text), \
                patch.object(client.frappe, "throw", create=True, side_effect=ValueError("blocked")):
            with self.assertRaisesRegex(ValueError, "blocked"):
                client.post_callback(self.settings, "http://callbacks.example.test/unsafe")
        self.post.assert_not_called()

    def test_real_service_confirms_only_successful_replay(self):
        for final in (response(204), response(401), response(503), requests.Timeout("synthetic")):
            with self.subTest(final=type(final).__name__):
                self.set_token("rejected-token")
                self.post.side_effect = [response(401), self.fresh_login(), final]
                doc = SimpleNamespace(name="TDX-TEST-AUTH", settings=self.settings.name,
                                      accepted_callback_url=None, rejected_callback_url=None,
                                      prepared_callback_url=self.url, picked_up_callback_url=None,
                                      prepared_notified=0, db_set=Mock())
                fake = SimpleNamespace(get_doc=Mock(side_effect=[doc, self.settings]))
                with patch.object(service, "frappe", fake), \
                        patch.object(service, "post_callback", client.post_callback), \
                        patch.object(service, "now_datetime", return_value="2026-10-27 12:00:00"):
                    if isinstance(final, requests.Response) and final.status_code == 204:
                        service.send_callback(doc.name, callback_event="prepared")
                        self.assertEqual(doc.db_set.call_args.args[0]["prepared_notified"], 1)
                    else:
                        with self.assertRaises(requests.RequestException):
                            service.send_callback(doc.name, callback_event="prepared")
                        doc.db_set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
