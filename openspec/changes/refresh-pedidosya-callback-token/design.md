## Approach
On the first callback response with status 401, compare-and-delete its rejected bearer token atomically in Redis, obtain the current token through the existing login/cache path, and repeat the same HTTP request once. There is no loop or recursion. Login errors and the second callback error propagate to the existing worker/recovery mechanism. No other status or network failure triggers immediate renewal.

## Cache isolation and concurrency
Use the existing integration-specific cache key and Frappe's site-prefixed make_key. A small Redis Lua compare-and-delete compares RedisWrapper's pickled token representation; it never removes a newer concurrent value. Clear only this key from frappe.local.cache before token reads/invalidation and use get_value(expires=True) to avoid request-local TTL bypass. Other integrations/sites are untouched. Cache invalidation errors propagate safely; they do not confirm a notification. Concurrent logins are not globally serialized; this change prevents deleting a newer token, not all duplicate logins.

## Reuse and review
Graphify's local graph was queried for post_callback, _access_token and send_callback, then actual source was inspected. Reuse the installed RedisWrapper serialization and the existing service notification-after-success path. The integration/QA specialist identified the request-local cache and compare/delete race; review the final diff again. No core Frappe/ERPNext changes.

## Contracts and risks
Validate callback HTTPS/allowlist before any login. Preserve TIMEOUT, JSON payloads and the absent body for prepared callbacks. A maximum of two callback requests is allowed per invocation, with one renewal path. A second 401 leaves the current token cached until the next invocation; it must not trigger a third request or mark notified. A callback returning 401 is assumed unauthenticated and may be replayed; provider-side callback deduplication remains necessary. Redis-wrapper serialization is version-specific and is covered against installed Frappe in development.

## Verification and safety
Standalone unittest mocks Redis/HTTP/document writes; do not run bench run-tests. Test concurrent replacement during compare-and-delete, other keys, stale local entries, refresh/login failures, second 401, other statuses and network failures, and real service flag behavior. Update the existing harness's old manual-cache-clear expectations to automatic invalid/expired-token recovery. Run only v15.local with synthetic inboxes, loopback HTTPS certificate validation and a private RQ queue. Keep scheduler paused, use directed recovery executions only, baseline operational counts/configuration, and verify cleanup even on failure. Never connect to production or the published receiver.

## Rollback and delivery
Branch fix/pedidosya-callback-token-refresh from local master c498d693e0998f126934b5b73845879307c3bcf5. Revert the new local commit if needed; no migration rollback. Remote publication, merge and deployment need separate explicit authorization.
