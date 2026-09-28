# Design

Add `TableOrder.deliver_completed_items(identifiers, expected_modified)` as
the native business procedure. Require `resto_mozo`, Table Order write access,
active restaurant company and existing order exception rules. Validate a
bounded, unique identifier list and lock the order/child rows before checking
current status. Use the ORM to set selected child rows to Delivered and call
`synchronize()` for the normal real-time update. No manual commit. The caller
must use a fresh order version; child-row status is rechecked under the lock.

The method is intentionally independent of Production Center configuration:
the waiter does not receive kitchen permission. It is not an HTTP endpoint;
TIX invokes it from its controlled-action confirmation on the same site.

DocTypes: Table Order, Order Entry Item. APIs: new document method (not
whitelisted directly). Hooks, fixtures, patches, reports: none. Affected file:
`restaurant_management/restaurant_management/doctype/table_order/table_order.py`
and focused tests. No migration. Disable the TIX action to stop MCP calls;
native rollback uses the request transaction. Existing delivered rows are
never reverted automatically.
