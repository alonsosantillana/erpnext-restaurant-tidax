## Context

Restaurant Tip already posts collection as debit to the collection asset and credit
to the configured tip liability. Its status model already reserves Settled, while
Propinas Resumen already supports checked rows and POS opening/closing context.

Graphify's local code-only graph confirms that the accounting lifecycle converges in
restaurant_tip.py and that report actions are isolated in propinas_resumen.js. The
implementation therefore extends those paths and adds one Journal Entry cancellation
hook; it does not touch POS invoicing or electronic invoicing.

## Accounting Decision

One settlement covers one waiter and one submitted POS closing:

- Debit: one line per Restaurant Tip against the shared liability account. Each line
  references that tip's submitted collection Journal Entry.
- Credit: one consolidated line to the company account configured for the chosen Mode
  of Payment.

The selected tip rows share one payout Journal Entry. The explicit references clear
the accounting trail from each receipt to its payment, while Restaurant Tip retains
the waiter and operational audit. A missing or unsubmitted collection entry blocks the
payout. The liability is not configured as a party account, so this avoids fake
Supplier or Employee masters.

## Authorization and Cash Session

Server checks are authoritative. Restaurant cashiers and administrators may settle;
waiters may not. A cashier may settle only a submitted closing belonging to that
cashier's opening. An administrator may settle any submitted closing for an accessible
company. Settlement requires a closed session because payout must reconcile against a
finalized set of collected tips.

## Transaction and Concurrency

The API deduplicates identifiers, limits batch size, locks all selected Restaurant Tip
rows in deterministic order with SELECT FOR UPDATE, and revalidates status and links.
Journal Entry creation and all tip updates share one savepoint. No manual commit is
performed. A second concurrent request observes Settled state after the first finishes.

## Reversal

A Journal Entry on_cancel hook finds tips linked through settlement_journal_entry and
restores them from Settled to Collected while clearing settlement metadata. Collection
entries remain submitted, so the tip liability becomes payable again. The hook ignores
unrelated Journal Entries.

## Reporting and UX

Propinas Resumen exposes Pagar al mozo only to management roles. The dialog summarizes
waiter, number of tips, total, and closing, then requests posting date and payment
method. The report displays settlement entry, payment method, actor, and timestamp only
when the caller can read Journal Entry; other settlement metadata remains visible.

## Rollback

Revert the app files and reload Restaurant Tip metadata only after cancelling any
settlement Journal Entries through their normal lifecycle. Do not delete submitted
entries or clear audit links manually.
