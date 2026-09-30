# Diagnose restaurant POS currency mismatch

## Problem

Preparing products for an off-premise Table Order fails with a POS currency mismatch, although the stored order, POS Profile and Price List values appear consistent. The current error does not reveal which invoice-validation stage or effective runtime values caused the rejection.

## Objective

Make the existing mismatch error identify the validation stage, POS Profile, selling Price List and their effective currencies so an operator can diagnose the source without a traceback.

## Scope

- Instrument only the mismatch branch in `apply_restaurant_pos_currency`.
- Label the Table Order invoice-build and POS Invoice validation call sites.
- Cover the diagnostic and unchanged successful path with focused tests.

## Exclusions

- No currency, price, tax, fiscal-payload or invoice calculation changes.
- No new logging, API, DocType, fixture, patch, migration or data write.
- No automatic retry or bypass of the mismatch validation.

## Impact and acceptance

The same invalid transaction remains blocked, now with a bounded, safe diagnostic containing the effective values and stage. Matching currencies preserve their current behavior. Frappe/ERPNext v15 compatibility is maintained. The fiscal and accounting risk is limited because no successful document path changes.
