# Native read-only cart quotation

## Why

The existing native quote_order requires phone and promised time for reviewed
orders. A price-only MCP cart must not invent these data or stage an order.

## What Changes

Add quote_cart for service_type/customer/items/address references only, reusing
the existing quote engine and all company/POS/customer/address/pricing guards.
Return computed net total, tax/charge rows and total without persistence. Preserve
quote_order's existing input/output and validation contracts.

## Impact

High risk financial calculation exposure, scoped to approved isolated source and
offline tests. Dependent TIX change: add-restaurant-readonly-cart-quote. No changes
to tax arithmetic, rates, masters, DocTypes, hooks, permissions, fixtures, patches,
migrations, installed source or services. No electronic invoicing/provider calls.

## Acceptance

Native pickup and delivery quotes, inclusive/exclusive taxes and configured service
charges match existing engine results. Delivery fee is included once. Unsupported
rules, unowned address and caller pricing fail closed. Native engine runs with
synthetic fixtures and all business writes/network blocked; full-order regressions pass.
