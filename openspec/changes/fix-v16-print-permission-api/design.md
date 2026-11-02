# Design
Native frappe.permissions.has_permission accepts print_logs=False. Its default prints permission diagnostics; omitting the keyword is not equivalent to the intended silent check before a legitimate scoped fallback. Keep imports and use the explicit native keyword. Do not catch TypeError, grant permissions or substitute a true result.

Files: restaurant_management/printing.py (queue_invoice_print), electronic_invoice.py (_check_user_access), test_printing.py expectations and a dedicated unittest regression module. Existing printing and electronic recovery OpenSpec designs remain authoritative for routing, payloads, attempts and idempotency. Confirmed existing Graphify nodes against actual source.

Tests bind to the real v16 function signature using autospec and exercise the real native callable with side effects mocked. Test native allow, fallback allow, deny and Guest for print/electronic gates; manual/automatic event keys and linked order context. Run in initialized read-only development transaction. Never enqueue real jobs, print tickets, submit invoices, or call provider APIs from tests.

Deployment requires source revision only and controlled web/module reload. No migrate, build, database/configuration changes or site backups. Shared production app receives the same minimal fix for installed sites. Reload idle queue workers if necessary for the electronic gate; never interrupt an active job. Human browser/physical-paper confirmation remains separate.

Rollback: revert the dedicated source commit through normal Git with a clean checkout, then reload the affected processes. No data restoration is necessary; the old incompatibility would return. Never replay existing print or electronic jobs as rollback.
