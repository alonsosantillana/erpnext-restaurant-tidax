# Validation

## Scope And Source

Date: 2026-11-01, America/Lima. Dedicated native-app branch:
`fix/restaurant-quote-scoped-settings-read`, based on master `cc765f9` with the
required installed quote prerequisite `8e0ac16`. The installed native checkout
remains clean at `8e0ac16`; installed TIX remains clean at `8fe8fe5`.
Neither primary branch, installed checkout, schema, permissions nor operational
configuration was changed. No migration, restart, channel activation, order,
reservation, invoice, payment, stock or fiscal dispatch was performed.

The old failed installed-quote test is historical evidence, not a passing test.
This correction is validated as candidate source only. Applying the candidate
to installed code requires a separately authorized operation.

## Automated Checks

- Native offline suite: 43 tests passed after the final security corrections.
  This includes 12 new adversarial tests over the 31-test prerequisite suite.
- Paired native/TIX adapter: 8 tests passed after the final corrections.
- Wider seven-module TIX/Web suite: 161 tests passed before the final two
  hardening corrections. The combined final-source run passed all 204 tests
  (43 native plus 161 TIX/Web) in 106.411 seconds. The 8 adapter tests above are
  included in 161, not additional unique tests. Existing Starlette/httpx and
  utcfromtimestamp deprecation warnings remain; no dependencies were changed.
- Strict OpenSpec validation passed before implementation and after hardening.
- Security specialist reviewed architecture, effective permissions, owner/field
  scope, applicable User Permissions, unsupported hooks and data isolation.
  Initial findings about Permission Query Server Scripts and metadata ordering
  were fixed and closed on re-review. No pending findings in that review scope.
- Native DatabaseQuery ordering methods are exercised with hostile sort metadata:
  the metadata fallback uses the forbidden customer field, while the projection
  uses only explicit name ascending ordering. The real-site SQL guard additionally
  rejects any Settings query containing default_customer or lacking fixed order.
- Local per-app Graphify code-only refresh: 2,575 nodes, 4,751 edges, 265
  communities. Output is ignored and not committed. No remote analysis/provider,
  dependency install or tool configuration change was used.

Offline fixtures supply storage, roles and metadata, not permission decisions or
tax arithmetic: actual native role/User Permission evaluators and whole-cart
price/tax helpers run. Guards deny site initialization, writes and networking.
Coverage includes restricted unrelated customers, unchanged full-document denial,
select/share-only denial, owner and field levels, record/Link scope and
applicable_for, strict empty fee Links, actor change/revocation, wrong/duplicate
bindings, virtual/type metadata, hooks/class overrides and Server Scripts.

## Approved Read-Only Site Trial

Used the existing prepared synthetic principal, customer/address/product fixtures
and bound company/POS. No new fixture or permission grant was introduced.
The helper explicitly verifies candidate import identity, starts a READ ONLY
transaction, guards SQL/document mutations, dispatch and external network, spies
the real native engine, rolls back and independently compares preservation state.
Quotes run as the restricted technical user, not Administrator; the latter is
used only for preservation inventory.

Latest private evidence receipt: `r9e2-full-readonly-quotes.x3mpsrl7` in the bench
private directory. The operation source, before/attempts/source/failure receipts
and independent check remain private and unversioned; no credentials, personal
data or full operational configuration is included here.

| Case | Observed result |
| --- | --- |
| Pickup, product quantity 2 | PEN 20.00 product amount and grand total |
| Native aggregate taxes and service charges | PEN 3.80 already included in 20.00, not IGV-only |
| Pickup fee | PEN 0.00, no fee line |
| Pickup repeat | Identical quote/fingerprint, two actual native engine calls |
| Delivery | Settings authorization passes; rejected before native arithmetic |
| Foreign customer | Rejected before native arithmetic |
| Foreign address | Rejected before native arithmetic |
| Caller-provided rate | Rejected before native arithmetic |
| Mutation/dispatch guard hits | Zero |
| Preservation | Same-transaction and independent connection checks passed |
| Admission/channel gates | All remain off |

The helper deliberately exits nonzero because the requested two-service trial is
not wholly successful. Delivery is not certified: the configured fee item belongs
to `Servicios`, outside the POS allowed product groups. The unchanged `_item`
catalog-group check rejects it. Its configured PEN 6.50 price existing does not
authorize ignoring that check. A fee eligibility/configuration decision and its
own approved scope are required; no item/profile/master changes were made here.
No claim of a second company's full quote, live Web/channel consent or fiscal
certification follows from this one prepared-principal native-function trial.

## Reproduction And Remaining Work

Use the bench environment with explicit candidate native and matching TIX
PYTHONPATH roots, running `python -B -m unittest`, not bench run-tests. Native
module: `restaurant_management.restaurant_management.test_order_quote`.
Paired modules: `test_restaurant_native_quote_adapter`,
`test_restaurant_web_native_consent`, `test_restaurant_web_consent_roundtrip`,
`test_channel_web_native_consent`, `test_channel_web`, `test_channel_web_orders`,
`test_channel_web_followup`. See the read-only quote guide for safety conditions.
Operational repetitions require the prepared private fixtures and preserved
read-only boundaries; this document does not authorize deployment or data edits.

- Final combined-source test rerun: 204 passed.
- Installation and primary merge: not performed, not part of this code approval.
- Full Delivery quote: blocked on independent fee-item catalog eligibility.
- Archive only after reviewing the final task evidence and consolidated spec delta.

Rollback: installed code/data are unchanged. Revert only this task commit after
review if needed; no inverse migration, permission removal or restore is needed.

## Publication

Implementation/test/documentation commit `5b22985` was pushed successfully to
`upstream/fix/restaurant-quote-scoped-settings-read`. This is a work-branch backup,
not a merge or installed update. A following documentation-only commit records
this publication and completed tracking without changing the tested runtime.
