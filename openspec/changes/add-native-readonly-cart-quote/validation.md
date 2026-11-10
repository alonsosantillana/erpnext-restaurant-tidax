# Validation

2026-11-10, branch feature/restaurant-readonly-quote, native base version-16 037c8a1.
Paired TIX change add-restaurant-readonly-cart-quote is based on version-16 7bf4e25.

Implemented quote_cart with the legacy authorization/calculation shared privately.
quote_order still validates contact/time and returns its unchanged result shape
and fingerprint. Cart output contains financial data and ordinal tax/charge rows,
not accounts, descriptions, contact data, source records or executable receipts.

## Verified Offline

- 25 cart tests plus 31 existing order tests run against synthetic native reads.
- Pickup/Delivery, exclusive/inclusive pricing and configured service-charge matrix;
  configured fee included once; legacy/cart monetary equality.
- Strict input keys/types, duplicate products, row/quantity limits, address ownership,
  native scope/permissions, unsupported rules and exception/flag restoration.
- Paired endpoint/client/security tests and regressions: 192 tests passed, including
  the above native suites. Guarded account/finalizer regression: another 235 tests
  passed, zero skips/errors/failures/protected I/O attempts. Total 427 on v16.
- External MCP client Python3.12: 37 tests passed separately.
- Actual runtime: Python3.14.3, Frappe16.55.2, ERPNext16.54.0. No site initialized.
- Independent paired static security review found no remaining blocking issue.
- Strict OpenSpec validation passed with existing Node22.23.1; diff checks clean.

The old native fixture initially failed on Frappe16's Local implementation, metadata
and native price-row shape. Reused only the necessary fixture compatibility changes
from existing preparation branches. The inclusive-tax fixture assertion now uses
the reviewed v16 value 38.14 rather than the historical engine value 38.13. Native
price/tax calculation code and tax/business configuration were not changed.
Expanded fixture traps include jobs, email and realtime as well as document/DB
writes, site initialization, network, FX insertion and POS validation/default hooks.

## Limits

No live site/ERP/channel/provider calls, native record changes, deployment, migrations,
permissions, service restarts, maintenance merge or installed-source update occurred.
Framework permission/metadata caches can populate during authorized real reads;
this is not a claim of zero cache writes. No application quote cache is added.
Synthetic test results do not certify the live customer's prices/taxes/address.

Apply/revert the paired TIX and native code together only in an authorized deployment.
No schema or data migration is needed. See paired TIX validation for full commands
and pending live-acceptance prerequisites.
