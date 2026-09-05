## 1. Specification and impact analysis

- [x] 1.1 Define authorization, shift, accounting, fiscal, audit, and concurrency requirements.
- [x] 1.2 Regenerate the Graphify code graph and verify the affected tip creation, posting, correction, invoice-cancellation, and reporting paths.

## 2. Data model and migration

- [x] 2.1 Add Restaurant Tip correction and cancellation audit fields and remove unique link constraints needed for versioned replacements.
- [x] 2.2 Reload Restaurant Tip metadata on the isolated v15.local site and verify obsolete unique indexes were removed.
- [x] 2.3 Confirm that no fixtures, patches, dependencies, core changes, or destructive data migration are required.

## 3. Server implementation and security

- [x] 3.1 Implement POST-only cancellation and rectification APIs with role, Company, shift, state, reason, and amount validation.
- [x] 3.2 Implement Journal Entry reversal, linked replacement creation, savepoint rollback, and row-level concurrency locking.
- [x] 3.3 Update POS Invoice cancellation to reverse every remaining active linked tip.
- [x] 3.4 Verify open-shift cashier access, closed-shift cashier denial, waiter denial, and administrator historical-access policy.

## 4. User interface and reporting

- [x] 4.1 Add cancel and rectify actions to the Restaurant Tip form with confirmation and refresh behavior.
- [x] 4.2 Add opening/closing filters, cancelled-tip visibility, audit columns, links, and row actions to Propinas Resumen.
- [x] 4.3 Ensure Journal Entry data is omitted when the report caller lacks read permission.
- [x] 4.4 Preserve pre-payment editing and removal of a proposed tip in the payment dialog.

## 5. Verification and regression

- [x] 5.1 Run Python, JavaScript, JSON, and diff-integrity checks for the changed files.
- [x] 5.2 Run reversible integration checks for successful rectification and cancellation, including accounting and audit links.
- [x] 5.3 Run reversible security checks for cashier open or closed shift behavior and waiter denial.
- [x] 5.4 Execute Propinas Resumen as cashier and verify totals and conditional Journal Entry visibility.
- [x] 5.5 Add permanent unit tests for validation, role security, rectification rollback, and cancellation of all active tip versions.
- [ ] 5.6 Add permanent database integration and concurrent-correction regression tests.
- [ ] 5.7 Complete browser smoke tests for form and report actions as cashier and restaurant administrator.

## 6. Deployment and closure

- [x] 6.1 Build assets, clear cache, and restart the authorized isolated v15.local environment.
- [ ] 6.2 Record final browser and automated-test results, deviations, and rollback readiness before closing the change.
- [ ] 6.3 Validate the completed OpenSpec change strictly and archive it after all tasks pass.
