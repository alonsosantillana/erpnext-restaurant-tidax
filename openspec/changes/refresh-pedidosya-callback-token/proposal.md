## Why
An outbound callback can receive HTTP 401 while its cached bearer token still has a local TTL. Current recovery retries reuse that rejected token until manual invalidation or expiry.

## What Changes
- Retry the same callback once after its first HTTP 401, refreshing only the rejected integration token.
- Atomically preserve a token concurrently renewed by another worker and avoid stale request-local token copies.
- Keep existing callback contracts, HTTPS restrictions, timeouts and notification-on-success behavior.
- Extend isolated unit and development HTTPS/RQ verification; no production access, remote publication, migration or general scheduler changes.

## Impact
Only the PedidosYa outbound client, isolated tests, development verification tool and this specification. No operational orders, accounting, permissions or schema changes.
