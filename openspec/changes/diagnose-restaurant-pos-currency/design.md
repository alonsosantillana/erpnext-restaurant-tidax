# Design

## Architecture

Add an optional diagnostic stage to `apply_restaurant_pos_currency`. The Table Order invoice builder and the POS Invoice revalidation hook supply distinct stage labels. The function compares the same values as before; only the existing `frappe.throw` message on mismatch changes. Include the POS Profile and Price List names and both currencies after escaping and bounding display values. Do not persist them to a log or document.

## Affected surface

- App/module: `restaurant_management`, Table Order/POS invoice currency validation.
- DocTypes read: POS Profile, Price List, Company. No DocType schema changes.
- Hook: existing POS Invoice validation hook calls `enforce_restaurant_pos_invoice_currency`; its registration stays unchanged.
- API/report/fixture/patch: none.
- Source: `restaurant_management/restaurant_management/doctype/table_order/table_order.py`.
- Tests: `restaurant_management/restaurant_management/doctype/table_order/test_table_order.py`.

## Security and integrity

Do not include customer, contact, RUC, token, secret or document contents. The error may show only bounded configuration identifiers and currency codes. No mutation occurs before this rejection and the normal invoice path remains unchanged. The error does not relax the fiscal or POS validation.

## Validation and rollback

Run OpenSpec validation and focused unit tests in an isolated worktree. In a non-production v15 site, retry the same prepare request and capture the new stage/values; confirm no token or document is created on rejection. A pure Python deployment requires process reload, not `bench migrate`. Rollback by reverting this commit and reloading processes; no data migration is needed.
