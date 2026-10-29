# Validation

29/10/2026 UTC (28/10/2026 America/Lima). User authorized the proposed correction:
per-company/POS templates may have tax only or tax plus a configured service
charge applying to both Pickup and Delivery. No fixed percentage or reclassified
account is introduced.

## Scope And Review

Native base e04b03d is the installed bounded-update prerequisite, fast-forwarded
from remote primary master cc765f9 into a new dedicated worktree. Only the
internal _taxes eligibility/evidence, its docstring, tests and this OpenSpec change
are edited. TIX companion branch fix/restaurant-web-tax-charge-label changes the
aggregate label and tests, not the schema or backend monetary contract.

Graphify local nodes _taxes/_calculate/quote_order were checked against source,
ERPNext validate_account_head/calculate_taxes_and_totals, native TableOrder
apply_pos_tax_inclusion, actual account field options and current hooks. No
new dependency/call path or production function is introduced; existing graphs
were consulted, not regenerated or versioned. No Repomix artifact was used.

Eligibility preserves all Tax support and adds only configured Income/Expense
Profit and Loss leaf charge accounts with the documented compatible types.
Company, read permission, disabled/group and row/rate support checks remain.
Root/report type enter fingerprint evidence; stale quotes must be recomputed.
No special company/account name or 13%/6.50 constant exists in production logic.
The wire tax field continues to mean native total_taxes_and_charges, not IGV only.

## Offline Native Tests

```bash
/home/erpnext/frappe-bench/env/bin/python -B -m unittest \
  restaurant_management.restaurant_management.test_order_quote
```

From this native worktree: 31 tests passed in 0.373 s. Five new tests include
eight service/inclusion/template combinations, configurable 7.25% charge and
compatible Income/Expense account types, scope/classification denials, row limits
and change-sensitive fingerprints. Native mutations/network/site-init/DB-write
guards remain untriggered; original fixtures are unchanged after quote generation.
Actual native POSInvoice constructor, low-level price helper and whole-cart tax
engine are exercised, not mocked arithmetic. Existing 26 tests still pass.

The red run before the correction rejected the configured service charges at the
old Tax-only guard (17 subtest errors). One hand-rounded expected Delivery amount
then differed by a cent: native Banker's Rounding rounds individual tax/charge
rows to 26.93 and 33.34, producing 60.27 / 316.77, not a single rounded aggregate
60.28 / 316.78. The expected fixture now asserts both native row amounts; no
production rounding logic was changed to satisfy the test.

Python source AST parsed for grammar 3.10/3.11/3.12. Static quote call-site check
found no save/insert/submit/commit/set_value/db_set/validate/new_doc/run_method/
default loading/FX call. Strict dedicated OpenSpec validation passed before the
implementation; final whitespace checks passed.

## Paired TIX Tests And Browser

161 relevant Python tests passed in 107.628 s using the native task worktree and
TIX task root/mcp_server/tests on PYTHONPATH: native quote adapter, native Web
consent, signed roundtrip, channel Web native consent, Web baseline, orders and
followup. Two new paired tests check combined service-charge monetary output and
unpriced handoff for a Payable account. Existing Starlette/httpx and utcfromtimestamp
deprecation warnings remain; dependencies were not changed.

Playwright/Chromium native-consent fixture passed four groups, including
1365x1000 desktop and 390x1000 mobile: exact aggregate wording, monetary contract,
explicit consent reset/expiry, retry/reload, late-read denial, bounded states,
assets and overflow checks. All browser requests are locally fulfilled; no ERP,
provider or listener is contacted. Desktop/mobile screenshots were visually
inspected under /tmp/tix-web-configured-charge-ui; no overlap or missing photo.
These screenshots contain synthetic amounts, not the site's configured fee.

## Bounded Read-Only Existing-Site Probe

A separate process imported the candidate _taxes source (asserted worktree path)
and initialized only the previously authorized existing site under the local-
storage network fence. Within START TRANSACTION READ ONLY, the already provisioned
technical principal could read the target template and both eligible rows:
10.5% Tax/Liability plus 13% charge/Expense. Business counts/max(modified) before
and after matched; all five R9E.2 gates remained off; transaction rolled back.
No full quote calculation, admission, master/config write or real order was run.
This establishes current-template eligibility, not native/Desk/SUNAT equivalence
or live end-to-end service certification. ADDERA identity/equivalence testing is
not claimed by the ERPCLOUD technical-principal probe.

## Preserved State And Remaining Work

Both installed worktrees remain clean on chore/restaurant-v15-bounded-update-r9e2.
No installed file, principal ref, database record, template, tax rate, fee price,
hook, scheduler, site configuration, permission, service or channel gate changed.
No migration, restart, bench run-tests, fiscal output, payment or provider call.

Pending after code review: a separately bounded update of the installed revisions,
then real read-only full quote/preview checks and Web consent/human approval in
the existing authorized site. Do not enable gates merely because offline tests
and the account eligibility probe passed. No new bench/site is required here.
