## Context

The initial tip feature stores a non-fiscal Restaurant Tip after POS Invoice creation
and posts a Journal Entry from the collection account to the configured tip liability.
This extension needs post-payment correction without editing submitted accounting or
changing the fiscal sale.

Graphify was regenerated from the current application using code-only extraction. Its
dependency graph confirms that TableOrder.make_invoice calls create_tip_record, that
rectification reuses post_tip_collection, and that manual cancellation, rectification,
and POS Invoice cancellation converge on _cancel_tip_document.

## Goals and Non-Goals

Goals:

- Make cancellation and rectification auditable, atomic, and role-controlled.
- Reuse the current tip posting and POS cancellation lifecycle.
- Reconcile tips by POS opening and closing.
- Preserve Company isolation and least privilege.

Non-goals:

- Alter POS Invoice, SUNAT/Nubefact payloads, taxes, discounts, gratuity rules, or series.
- Implement waiter payout or settlement reversal.
- Modify Frappe or ERPNext core.

## Architecture and Decisions

### Versioned correction instead of editing

Submitted tips are never edited in place. Cancellation reverses their submitted
Journal Entry. Rectification first cancels the original and then calls the existing
posting service to create a linked replacement. This preserves accounting history and
makes the latest active version explicit.

Alternatives rejected:

- Editing amount and Journal Entry rows in place destroys the audit trail.
- Posting only a delta makes operational reporting and later cancellation ambiguous.
- Changing the POS Invoice would incorrectly turn a non-fiscal correction into a
  fiscal-document mutation.

### Server authorization

Whitelisted POST APIs call a shared permission function. It accepts restaurant cashier
and restaurant administrator roles, plus system administration compatibility, then
checks Company access. Cashiers are limited to an opening without a submitted closing;
restaurant administrators may correct historical eligible tips. Client-side button
visibility is convenience only and is not a security boundary.

### Transaction and concurrency model

Each operation creates a savepoint, obtains the current tip with parameterized
SELECT FOR UPDATE, and revalidates status and replacement links after locking.
Direct SQL is limited to row locking because the Frappe ORM does not expose an
equivalent portable document lock. All mutations still use standard document
lifecycle methods. There is no manual commit; exceptions roll back to the savepoint.

Rectification treats original cancellation, replacement creation, and replacement
posting as one transaction. A failure restores the original active state.

### Reporting

Propinas Resumen reads Restaurant Tip as its source of truth, joins POS opening/closing
context, and provides an optional cancelled-record view. It checks Journal Entry read
permission before defining or returning that column. Report actions invoke the same
server APIs as the document form.

### Realtime behavior

The correction APIs return the resulting state and the UI refreshes the form or report.
No new realtime event is necessary because this is an administrative workflow rather
than a kitchen order-state transition.

## Fiscal and SUNAT Boundary

Tips remain outside POS Invoice item totals, taxes, discounts, paid amount, change,
series, gratuity calculations, and the ovenube_peru/Nubefact payload. Cancelling or
rectifying a tip does not cancel, amend, resend, or regenerate the electronic invoice.
The original POS Invoice reference is retained only for traceability.

## Data Model and Migration

Restaurant Tip adds predecessor and replacement links plus cancellation audit metadata.
The previous unique constraints on Table Order and POS Invoice links are removed so a
cancelled original and one active replacement can coexist. Business validation
enforces at most one active version.

The DocType reload applies metadata and index changes. No destructive patch or data
rewrite is required. Existing tips have empty audit fields and retain their status.

## Fixtures, Hooks, Dependencies, and Upstream

- No new fixtures, hooks, scheduled jobs, packages, or services.
- No upstream code is ported; the change is local to restaurant_management.
- Existing role fixtures continue to provide cashier and administrator roles.

## Rollback Plan

- Before deployment, revert application files and reload metadata if required.
- After corrective entries exist, first reverse them through the supported tip
  lifecycle, then revert code. Do not delete submitted Journal Entries or audit rows.
- POS Invoices and electronic documents need no rollback because they are untouched.

## Risks and Mitigations

- Double correction: row lock plus state revalidation and active-tip validation.
- Partial accounting reversal: savepoint and standard Journal Entry cancellation.
- Unauthorized history changes: server role, Company, shift, and status checks.
- Report data exposure: omit Journal Entry data without DocType read permission.
- Historical ambiguity: bidirectional correction links and cancellation audit fields.

## Test Matrix

| Area | Case | Expected result |
| --- | --- | --- |
| Unit | Invalid reason and invalid corrected amount | Request rejected without mutation |
| Integration | Rectify active tip | Original cancelled; linked replacement and JE submitted |
| Integration | Replacement posting failure | Full transaction rolled back |
| Security | Cashier, administrator, waiter, foreign Company | Only allowed role and scope succeeds |
| Concurrency | Two changes to one tip | One succeeds; one active version remains |
| Accounting | Cancel collected tip | Collection JE cancelled; POS Invoice unchanged |
| Report | Filter by opening or closing and include cancelled | Correct rows, totals, and audit context |
| Regression | Pay with zero tip and cancel POS Invoice | No tip posting; every active tip reverses |
| Browser | Form and report actions | Confirmation, refresh, and errors are usable |

## Validation Evidence

- Python and JavaScript syntax checks completed.
- Restaurant Tip metadata reloaded on the isolated v15.local site.
- A rectification was executed inside a reversible transaction and verified to create
  the linked replacement and Journal Entry; rollback restored the fixture.
- An open-shift cashier cancellation succeeded inside a reversible transaction.
- A closed-shift cashier and a waiter were both rejected.
- Propinas Resumen executed as cashier, returned the expected active total, and omitted
  the Journal Entry column when permission was absent.
- Permanent database integration/concurrency tests and final browser smoke testing
  remain tracked tasks; six focused unit/security regression tests now pass.

## Open Questions

None. The agreed role policy is cashier during an open shift and restaurant
administrator after closing; waiters cannot perform post-payment tip corrections.
