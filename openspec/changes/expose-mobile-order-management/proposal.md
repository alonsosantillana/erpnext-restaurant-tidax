# Change: Expose stable restaurant order management to Mobile

## Why
Resto Tix Mobile must reuse the mature `restaurant_management` behavior without granting arbitrary document or method access.

## What Changes
- Add a permission-aware customer search.
- Add idempotent, version-checked customer, guest-count and discount mutations.
- Add guarded facades over `TableOrder.divide` and `TableOrder.transfer`.
- Return all authorized active accounts for each table.

## Impact
The facade and OpenAPI contract expand; core restaurant methods remain the source of business truth.
