# Native Dine-In Table Service

## Problem and goal

Production Centers can mark dishes Completed, but their status transition API
requires the kitchen role. Dine-in waiters need a separate, authorized way to
record that specific completed dishes were delivered to a table.

## Scope

- Add one native Table Order method for Completed -> Delivered on selected rows.
- Require an active dine-in order, an authorized waiter, current version, and
  row membership/status; preserve every other row and financial value.
- Notify the existing order channel after a successful transition.

## Exclusions

No changes to P3/P5 status maps, Restaurant Fulfillment, billing, payments,
stock, accounting, fiscal integrations, DocTypes, fixtures, or existing rows.

## Impact and acceptance

Risk: medium (operational permissions and concurrent row updates). A waiter
can deliver only eligible rows on an order they may update; another order,
stale state, repeated delivery, and a non-waiter are rejected. No unrelated
rows or totals change. Unit tests cover these cases.
