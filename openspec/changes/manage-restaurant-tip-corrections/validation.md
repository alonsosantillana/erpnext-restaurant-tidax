## Validation environment

- Site: v15.local (isolated local Frappe/ERPNext v15 site).
- Graphify: code-only graph regenerated from the application root; 2,414 nodes,
  3,770 edges, and 269 communities.
- OpenSpec: change validated in strict mode with all four required artifacts present.

## Automated checks

- Python compilation passed for restaurant_tip.py and test_restaurant_tip.py.
- Six permanent Restaurant Tip unit tests passed. They cover cancellation reasons,
  closed-shift cashier denial, historical administrator access, waiter denial,
  rectification rollback, and reversal of all active tip versions when an invoice is
  cancelled.

## Reversible integration checks

- Rectification of an active tip created a linked replacement and submitted Journal
  Entry; transaction rollback restored the original fixture.
- Cancellation by a cashier in an open shift succeeded; rollback restored the fixture.
- A cashier was rejected for a tip belonging to a closed shift.
- A waiter was rejected from post-payment tip management.
- Propinas Resumen executed under a cashier user, returned the expected active total,
  and omitted Journal Entry data when that user lacked read permission.

## Deviations and pending validation

- Browser smoke tests for the Restaurant Tip form and Propinas Resumen actions remain
  pending with real cashier and restaurant administrator sessions.
- A permanent database concurrency test remains pending; row locking was confirmed by
  code review and Graphify impact analysis, while transactional behavior was exercised
  through reversible integration checks.
- No migration patch, fixture change, dependency, upstream port, or core-app change was
  necessary for this correction extension.

## Rollback readiness

The code and metadata can be reverted before use. Once a corrective tip has posted,
its Journal Entry and audit chain must be reversed through the supported lifecycle;
submitted accounting records must not be deleted.
