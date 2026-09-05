## Why

Restaurant Management could collect and report tips, but it had no controlled way to
correct an amount or cancel a tip after payment. Editing a submitted record or its
Journal Entry directly would break the audit trail and could leave reporting,
liability accounting, and the original collection out of sync.

## Objective

Provide an auditable cancellation and rectification workflow for restaurant tips,
restricted to cashier and restaurant administrator roles, while keeping the fiscal
POS Invoice and the Nubefact/SUNAT document unchanged.

## What Changes

- Add server APIs to cancel a collected tip and to replace it with a corrected tip.
- Cancel the original tip Journal Entry before marking the tip as cancelled.
- Record reason, actor, timestamp, predecessor, and replacement links.
- Allow a cashier to manage tips only while the related POS opening is active; allow
  a restaurant administrator to correct historical tips.
- Reject waiter access, settled tips, invalid companies, invalid amounts, and
  concurrent attempts to change the same active tip.
- Add actions to the Restaurant Tip form and Propinas Resumen report.
- Add opening/closing filters and cancellation/correction audit columns to the report.
- Preserve the existing ability to change or remove a tip before payment.

## Scope

- App: restaurant_management.
- Modules and DocTypes: Restaurant Tip, POS Opening Entry, POS Closing Entry,
  POS Invoice, and Table Order.
- APIs: cancel_restaurant_tip, rectify_restaurant_tip, and the existing
  POS Invoice cancellation integration.
- Report: Propinas Resumen.
- Frontend: Restaurant Tip form actions, Propinas Resumen actions, and the existing
  restaurant payment form.

## Out of Scope

- Modifying a submitted POS Invoice, its items, taxes, discounts, series, or total.
- Reissuing or cancelling the electronic comprobante in Nubefact/SUNAT.
- Paying out or settling tips to waiters.
- Changing the existing accounting model for initial tip collection.

## Impact and Risk

- Risk: high, because the change affects accounting entries and submitted records.
- Compatibility: Frappe v15 and ERPNext v15; no core app modifications.
- Security: every API validates caller role, Company access, shift state, and
  document state on the server.
- Integrity: cancellation and rectification run atomically and lock the active tip
  row to prevent duplicate corrections.
- Tax: the POS Invoice and electronic payload remain untouched; tips continue outside
  sale taxes and discounts.
- Dependencies: no new package, external service, hook, or upstream port is required.

## Migration and Rollback

- Reload Restaurant Tip so the new audit fields and non-unique links are available.
  Existing records remain valid.
- Application rollback restores the prior Python, JavaScript, report, and DocType
  definitions. Corrective tips already posted must be reversed through the documented
  accounting lifecycle rather than deleted.

## Acceptance Criteria

- An authorized cashier can cancel or rectify an unsettled tip from an open shift.
- A restaurant administrator can manage an eligible historical tip after closing.
- A waiter cannot invoke either operation.
- Cancellation reverses the submitted Journal Entry and records audit metadata.
- Rectification creates a linked replacement with a corrected positive amount and
  rolls the whole operation back if the replacement cannot be posted.
- Propinas Resumen can be filtered by opening/closing and shows active or cancelled
  records without exposing Journal Entries to users lacking permission.
- The related POS Invoice and Nubefact/SUNAT representation are not changed.
