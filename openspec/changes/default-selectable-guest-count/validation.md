## Validation record

Date: 2026-08-31

### Completed

- OpenSpec strict validation with Node 20: passed.
- Python compilation for the modified controller and test: passed.
- JavaScript syntax check for `table-order-class.js`: passed.
- JSON parsing for the Table Order and Desk Form definitions: passed.
- `git diff --check`: passed.
- Focused Frappe test
  `test_add_order_returns_persisted_state_for_client_reconciliation`: passed
  on `v15.local`.

### Deployment completed

- `bench --site v15.local migrate`: passed.
- `bench build --app restaurant_management`: passed.
- `bench --site v15.local clear-cache`: passed.
- Database metadata verification: `Table Order.guest_count` is Int/default 1
  and the Desk Form field is Select/default 1/required.
- Manual smoke test approved by the user: a new table order starts at one guest,
  the guest count is selectable and saving the new value behaves correctly.

No deviation from the approved scope was introduced.
