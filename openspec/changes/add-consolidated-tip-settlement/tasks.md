## 1. Specification and impact

- [x] 1.1 Define accounting, role, shift, audit, concurrency, and reversal rules.
- [x] 1.2 Use Graphify and source review to identify the affected tip and report paths.

## 2. Data model and server

- [x] 2.1 Add Restaurant Tip settlement audit fields.
- [x] 2.2 Implement consolidated settlement with role, company, waiter, closing, state,
  account, and submitted collection-entry validation; reference each receipt from its
  payout debit line.
- [x] 2.3 Restore linked tips when the settlement Journal Entry is cancelled.

## 3. Report UX

- [x] 3.1 Add the Pagar al mozo bulk action and confirmation dialog.
- [x] 3.2 Add settlement audit columns with conditional Journal Entry exposure.

## 4. Verification and deployment

- [x] 4.1 Add unit tests for accounting construction, validation, rollback, authorization, and reversal.
- [x] 4.2 Run Python, JavaScript, JSON, OpenSpec, and Graphify checks.
- [x] 4.3 Reload metadata, clear cache, build assets, restart, and run reversible site checks.
- [ ] 4.4 Complete browser smoke testing for cashier and restaurant administrator.
