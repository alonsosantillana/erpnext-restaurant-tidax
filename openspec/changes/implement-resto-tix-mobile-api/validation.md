# Validation

## Scope validated

- Frappe facade `restaurant_management.mobile_api.v1`.
- OpenAPI 3.1 contract for the FastAPI BFF.
- Private `Restaurant Mobile Request` metadata and controller.
- Authentication context, contextual authorization, input bounds, optimistic concurrency and persistent idempotency at unit level.
- No payment, POS Invoice or electronic-invoicing endpoint was added.
- No hook, fixture, patch, core app, site configuration or commercial runtime data was changed.

## Commands and results

```text
python3 -m py_compile restaurant_management/mobile_api/test_v1.py restaurant_management/mobile_api/v1.py
```

- Result: successful.

```text
/home/erpnext/frappe-bench/env/bin/python -m unittest restaurant_management.mobile_api.test_v1 -v
```

- Result: 16 tests passed in 0.109 seconds.
- The tests initialize Frappe metadata context but use mocks for database operations; no business data was read or written.

```text
/home/erpnext/.nvm/versions/node/v22.23.1/bin/node /home/erpnext/.local/bin/openspec validate implement-resto-tix-mobile-api
```

- Result: `Change 'implement-resto-tix-mobile-api' is valid`.

```text
bench --site v15.local migrate
bench --site v15.local execute frappe.db.exists --args '["DocType", "Restaurant Mobile Request"]'
```

- Result: migration completed successfully and the DocType lookup returned `Restaurant Mobile Request`.
- No commercial document or test fixture was created.

The approved QA OAuth Client was configured with Authorization Code, explicit
consent, the custom application callback and minimum `all` scope. A temporary
end-to-end run through the real FastAPI BFF validated authorization, S256 PKCE
exchange, bearer acceptance and revocation. The generated code, token and login
session were removed after the test; no token or generated client secret was
printed or persisted outside Frappe.

A second read-only run used an enabled QA waiter and validated the complete
authorized context path through the BFF:

- OAuth authorization and S256 PKCE exchange: passed.
- Context matched the authenticated waiter: HTTP 200.
- Authorized restaurant scope: 2 rooms and 4 tables.
- Revocation made the bearer unusable: HTTP 401.
- OAuth bearer and authorization-code counts for the QA client returned zero
  after cleanup.
- No order, table state or other commercial record was created or modified.

## Residual validation

- OAuth2/PKCE, real waiter context/tables and revocation passed end to end; expiry and cross-user scope remain pending.
- Double-tap, retry-after-timeout and simultaneous-device cases require an isolated integration site.
- Catalog/tax/total parity and Restaurant Manage, kitchen, printing and POS regression remain pending.
- Production remains blocked until a valid HTTPS origin and revocable OAuth client are configured.
