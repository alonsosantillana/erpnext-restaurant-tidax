# Restore invoice print authorization under v16
## Why
The existing manual POS Invoice print endpoint crashes before authorization because frappe.permissions.has_permission does not accept raise_exception. The same invalid keyword exists in the electronic-invoice access gate.
## What Changes
Replace only raise_exception=False with the native print_logs=False in those two access gates; update matching test expectations and add signature-aware authorization regression tests. Preserve all callers, authorization decisions, scoped fallbacks, routing and idempotency.
## Impact
One own app, no Frappe/ERPNext core, roles, permissions metadata, DocTypes, fixtures, patches, tax payloads, invoice values or historical edits. No provider calls or physical print during automated testing. User explicitly requested fixing printing after the diagnosed shared incompatibility on 2026-11-02. Risk is authorization compatibility, not a new access policy. Development tests and specialized review precede production deployment.
## Acceptance
Authorized printing reaches the unchanged queue; unauthorized and unauthenticated callers remain blocked. Direct native v16 signature integration must pass. Provider synchronization behavior remains unchanged.
