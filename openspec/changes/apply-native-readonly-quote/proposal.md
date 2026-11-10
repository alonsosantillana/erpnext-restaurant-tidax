# Apply Native Cart Adapter

## Why
The owner approved installing the reviewed native cart adapter with TIX's read tool.

## What Changes
Align the clean installed source from 037c8a1 to reviewed 8138a20. Native entry
and shared calculation changes are limited to the already reviewed quotation work.

## Impact
High risk code application only. No DocTypes, hooks, grants, settings, migrations,
services, tax arithmetic, stock, invoices, orders or providers are changed.
Paired TIX procedure: apply-restaurant-readonly-quote. No maintenance merge.

## Acceptance
Installed source matches the reviewed pin, native/paired offline tests pass and
the existing read/auth controls remain. Real quote acceptance needs actual owner-
approved customer/address data and the updated MCP connection.
