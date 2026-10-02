# Design

## Architecture

Add an optional `allow_offpremise=False` argument to
`mobile_api.v1._validate_order_access`. The room bypass applies only when the
caller opts in and `service_type` is Delivery or Pickup with no room or table.
The company/POS Profile comparison, `check_exceptions` order authorization,
and open-order check remain unchanged. `create_invoice` opts in; the TIX R8D
preparation calls the same validator with the flag. All other callers retain
the default and therefore their current access behavior.

## Surface and Dependencies

Apps: `restaurant_management` and coordinated TIX R8D caller. DocTypes:
`Table Order`, `POS Invoice`, `Restaurant Fulfillment` are read or used by the
existing flow; no schema change. Files: `restaurant_management/mobile_api/v1.py`,
`restaurant_management/mobile_api/test_v1.py`, TIX R8D action and its contracts.
No hooks, fixtures, patches, reports or migrations. Frappe/ERPNext v15 behavior
is preserved. Source verification is required because the local Graphify graph
predates this change.

## Security and Reversal

The opt-in never skips company, profile, document permission or owner/exception
checks. It rejects an off-premise order carrying a room or table, instead of
treating it as a roomless order. No raw customer data or credentials are logged.
No new transaction, commit, realtime event or external call is introduced.
Revert both coordinated code changes to restore the old gate; already issued
invoices require existing fiscal/accounting cancellation and are not reversed
by code rollback.

## Verification

Unit tests cover authorized Delivery/Pickup billing, default off-premise
denial, unauthorized Dine In room, mismatched company/profile, malformed
off-premise room/table and native order permission failure. Run TIX R8D and
full MCP contracts, strict OpenSpec validation, then an operator-controlled
preview in an isolated v15 test site. No live invoice in code validation.
