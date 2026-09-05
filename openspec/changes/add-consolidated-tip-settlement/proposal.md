## Why

Restaurant tips are collected into a liability account, but there is no controlled
way to record their later payment to the waiter. Leaving the liability open or
posting manual entries makes it difficult to prevent duplicate payouts and reconcile
each payment with the underlying tips and POS cash session.

## Objective

Allow authorized restaurant cashiers and administrators to select collected tips for
one waiter and settle them with one consolidated Journal Entry, preserving complete
accounting and operational traceability.

## What Changes

- Add settlement audit fields to Restaurant Tip.
- Add a POST-only API that locks and validates selected tips, resolves the selected
  payment method account, and creates one balanced consolidated Journal Entry whose
  debit lines reference the original collection entries.
- Mark every included tip as Settled and link it to the shared settlement entry.
- Add a Pagar al mozo action and settlement columns to Propinas Resumen.
- Restore tips to Collected if their settlement Journal Entry is cancelled.
- Prevent cancellation or rectification while a tip remains settled.

## Scope

- App: restaurant_management.
- DocTypes: Restaurant Tip, Journal Entry, Mode of Payment, POS Opening Entry, and
  POS Closing Entry.
- Report: Propinas Resumen.

## Out of Scope

- Paying several waiters in one settlement.
- Payroll, employee advances, commissions, or withholding calculations.
- Changing POS Invoice, taxes, SUNAT/Nubefact documents, or the original collection
  Journal Entries.

## Acceptance Criteria

- A cashier or restaurant administrator can settle multiple collected tips belonging
  to one waiter, company, liability account, and submitted POS closing.
- Exactly one Journal Entry debits Tips Payable once per tip with a reference to its
  submitted collection entry, and credits the selected cash/bank account once for the
  selected total.
- Concurrent or repeated attempts cannot pay the same tip twice.
- Every settled tip records the Journal Entry, payment method, account, actor, and time.
- Cancelling the settlement Journal Entry returns its linked tips to Collected.
- Waiters and unauthorized users cannot invoke settlement APIs.
