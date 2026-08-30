## 1. Specification and baseline

- [x] 1.1 Review current payment controls, tip controls, keypad and invoice payload.
- [x] 1.2 Query Graphify and confirm PayForm dependencies against source and Desk Form.
- [x] 1.3 Define compact, mixed-payment and rollback behavior.
- [x] 1.4 Validate the OpenSpec change strictly.

## 2. Compact payment editor

- [x] 2.1 Add allocation state and pure total-normalization helpers.
- [x] 2.2 Replace permanent per-method inputs with selector and active amount.
- [x] 2.3 Add compact allocation summary with edit, delete and add-next actions.
- [x] 2.4 Connect the numeric keypad and preserve the existing invoice payload.
- [x] 2.5 Keep tip controls independent and unchanged functionally.

## 3. Presentation and accessibility

- [x] 3.1 Add isolated responsive styles with bounded summary height.
- [x] 3.2 Include labels, button text and pending/change indicators independent of color.
- [x] 3.3 Load the new stylesheet only in Restaurant Manage.

## 4. Validation and deployment

- [x] 4.1 Add Node tests for normalization, totals, duplicates and removals.
- [x] 4.2 Validate JavaScript syntax, tests, diff and OpenSpec.
- [x] 4.3 Regenerate the local Graphify code graph without versioning artifacts.
- [x] 4.4 Build app assets and clear cache on authorized `v15.local`.
- [x] 4.5 Smoke-test simple, mixed, edit, delete, keypad and tip flows for both companies.
- [x] 4.6 Record final files, commands, results, deviations and Git status.
