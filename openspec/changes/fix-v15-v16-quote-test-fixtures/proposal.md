# Proposal

## Problem And Scope
The offline native quote fixture uses v15-private Local storage and a historical
document module patch path. Its setup fails on v16 before paired TIX assertions
run. User approved fixture adaptation and offline regression on both versions.
Change restaurant_management/restaurant_management/test_order_quote.py and docs
only. Preserve the real POSInvoice, price helper, native tax engine and all
expected arithmetic. Risk: medium test-isolation/coverage risk, not a change to
pricing rules, tax rates or business execution.

## Dependencies And Exclusions
Base: version-16 c96d967; installed documentation branch remains untouched.
Companion TIX change fix-v15-v16-approval-test-fixtures starts at da2dc08.
No application source, API, hooks, DocType, database fixtures, permissions,
patches, migration, site configuration, dependency or service modifications.
No real invoices, prices, orders, payments, regional provider or live requests.

## Acceptance
Native quote and paired TIX adapter tests pass with synthetic fixtures on v15
and v16. Public context isolation restores caller values after success/failure.
Native tax calculations and side-effect guards remain intact. Record evidence
without claiming installed-site or regional tax certification.
