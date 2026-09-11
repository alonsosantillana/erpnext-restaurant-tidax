# Validation

## Scope validated

- Frappe facade `restaurant_management.mobile_api.v1`.
- OpenAPI 3.1 contract for the FastAPI BFF.
- Private `Restaurant Mobile Request` metadata and controller.
- Authentication context, contextual authorization, input bounds, optimistic concurrency and persistent idempotency at unit level.
- No payment, POS Invoice or electronic-invoicing endpoint was added.
- No hook, fixture, patch, core app, site configuration or runtime data was changed.

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

## Residual validation

- OAuth2/PKCE and delegated-token behavior must be exercised through the FastAPI BFF.
- Double-tap, retry-after-timeout and simultaneous-device cases require an isolated integration site.
- Catalog/tax/total parity and Restaurant Manage, kitchen, printing and POS regression remain pending.
- `bench migrate` is required to install `Restaurant Mobile Request`; it was not run because it requires explicit authorization.
- Production remains blocked until a valid HTTPS origin and revocable OAuth client are configured.
