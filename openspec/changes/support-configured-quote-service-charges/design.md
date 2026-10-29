# Design

## Source And Dependencies
master is the remote primary (cc765f9). The installed bounded-update line is
e04b03d, containing the pending read-only quote. Create a task worktree from master
and fast-forward that existing prerequisite, preserving installed/mainline refs.
The existing per-app Graphify graph located _taxes, _calculate and quote_order;
source confirmed the sole blocker is the Tax-only account check. Native ERPNext
validate_account_head validates company and leaf status, not Tax-only. Native
TableOrder.apply_pos_tax_inclusion makes the POS profile's inclusion flag apply
to every loaded row; preserve that existing calculation behavior.

## Eligibility And Calculation
Preserve existing Tax support. Additionally require charge account root_type to
be Income or Expense, report_type Profit and Loss, and account_type blank,
Chargeable, Income Account, Expense Account, Direct/Indirect Income or Expense.
Do not accept Bank, Cash, Receivable, Payable, Stock, valuation, round-off or other
special accounts merely because they appear in a template. These are support
limits for read-only quoting, not accounting advice or replacement validation.
The account must be readable, enabled, same-company and non-group. The template
is still enabled/same-company, maximum ten unique nonnegative bounded On Net Total
rows, with no deduction/unsupported recomputation. No account name or fixed rate
identifies a service charge. Use configured rows/rates for each service/profile.

Append root_type/report_type to account fingerprint evidence. Eligibility changes
therefore invalidate stale quote authority even if totals/modified time match.
Keep real ERPNext calculation once per unsaved whole-cart POSInvoice; do not call
save/validate/default loading. Keep tax as total_taxes_and_charges, including
configured service charges and inclusive breakdown; never add that amount again
to already-inclusive line totals. TIX labels the unchanged aggregate accurately.

## Files, Permissions And Data
Only order_quote.py, test_order_quote.py and this specification change in this app.
Companion TIX scope is orders.js, its browser assertion, its dedicated OpenSpec
and status guidance. No hooks, DocTypes, API schema, fixtures, migrations or
permissions change in either app. No site or data is accessed by offline tests.

## Tests And Rollback
Guarded unittest uses actual native numeric calculation and synthetic reads.
Matrix: Pickup/Delivery, inclusive/exclusive, tax-only/tax-plus-charge, 6.50 fee,
other configurable rates and Income/Expense classifications. Negative cases:
foreign/denied/disabled/group accounts, unsupported type/root/report, duplicate,
deducted, negative and over-limit rates. Check unchanged fixture documents and
fingerprints for supported account classification/rate changes.
Browser fixture checks the existing quote display on desktop/mobile with no ERP
or external requests. Live metadata/localization/native-admission equivalence
remains separate on the existing authorized site, not a new bench requirement.
Rollback is to revert only task commits after review; no inverse migration or
master-data restoration. Keep gates off; runtime update requires a separate step.
