# Proposal

The user accepted version-specific offline inclusive-tax expectations: 38.13 for
ERPNext v15 and 38.14 for v16 at unchanged total 250. Prior fixture correction
exposed a real native rounding difference, not a pricing defect to patch.

Change test_order_quote.py and test documentation only, based on 5296efd.
Add a fixed test-only expectation helper, exact oracle/unknown-major cases and
use it in the native inclusive assertion. Companion TIX change has the same ID
and consumes that helper. Risk: medium test-coverage risk; no production math,
rates, monetary inputs, API, DocType, permissions, hooks, database fixtures,
patches, migrations or operational configuration are modified.

Acceptance: focused native/paired and backend regressions pass on both inspected
versions with exact values and all guards retained. Unknown majors fail closed.
No broad fiscal, live-site, deployment or package compatibility claim is made.
