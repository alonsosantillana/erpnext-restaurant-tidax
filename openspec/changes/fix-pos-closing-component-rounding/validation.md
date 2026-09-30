# Validation

Date: 2026-09-29
Site: `v15.local`

## Automated checks

- `restaurant_management.restaurant_management.test_pos_invoice_merge`: 10 tests passed.
- `restaurant_management.restaurant_management.test_pos_closing_expenses`: 4 tests passed.
- Python compilation passed for implementation and tests.
- `git diff --check` passed.
- OpenSpec strict validation passed with Node.js 20.20.2.
- Graphify code-only graph refreshed: 3104 nodes, 4751 edges, 356 communities.

## Live-data read-only validation

`BV-BRE2-000022` was loaded without saving changes and mapped as consolidation
components:

- item lines: 11;
- non-zero tax rows: 2;
- component sum before reconciliation: S/ 249.97;
- POS Invoice grand total: S/ 250.00;
- calculated bounded tolerance: S/ 0.07;
- residual applied to the mapped target: S/ 0.03;
- component sum after reconciliation: S/ 250.00;
- final residual: S/ 0.00;
- persisted POS Invoice grand total remained S/ 250.00.

## Pending operational check

Retry submission of `POS-CLO-ECS-2026-00012` from the user session and verify the
created consolidated Sales Invoice before marking task 3.3 complete.
