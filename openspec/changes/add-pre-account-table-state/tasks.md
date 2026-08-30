## 1. Specification and baseline

- [x] 1.1 Review current ACCOUNT queue, Table Order mutations, table aggregation and realtime channels.
- [x] 1.2 Consult Graphify locally and confirm findings against source code and DocTypes.
- [x] 1.3 Define persistence, invalidation, multi-order aggregation and rollback behavior.
- [x] 1.4 Validate the OpenSpec change.

## 2. Persistent domain state

- [x] 2.1 Add additive audit and signature fields to Table Order.
- [x] 2.2 Implement a deterministic monetary signature and validation-time invalidation.
- [x] 2.3 Mark pre-account only after ACCOUNT is durably enqueued with effective permissions.
- [x] 2.4 Include pre-account state in authoritative order and table payloads.

## 3. Realtime and interface

- [x] 3.1 Publish the aggregate table state through existing after-commit notifications.
- [x] 3.2 Reconcile pre-account state in RestaurantObject without local-only assumptions.
- [x] 3.3 Add accessible requested and outdated visual states without affecting Production Center.

## 4. Validation

- [x] 4.1 Add unit tests for signature stability, monetary invalidation and non-monetary preservation.
- [x] 4.2 Add tests for queue success/failure and table aggregation across multiple active orders.
- [x] 4.3 Validate Python, JavaScript, JSON, CSS diff and OpenSpec.
- [x] 4.4 Build assets and run targeted Frappe tests on the authorized v15 test site.
- [x] 4.5 Run migrate and smoke-test requested, outdated, reprint, transfer and payment behavior.
- [x] 4.6 Record final files, commands, results, deviations and Git status.
