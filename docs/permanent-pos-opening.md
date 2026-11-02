# Permanent restaurant POS openings (v16)

Restaurant Company Settings → Allow Permanent POS Opening is disabled by default. An authorized settings administrator may enable it only after reviewing the operational policy. It applies solely to that company's primary POS Profile; other profiles keep native same-day validation.

A single submitted Open entry is required, matching the invoice company and existing opening reference. Future starts, missing and duplicate openings remain blocked. This option does not close cash sessions, change dates or consolidate invoices. It changes only the same-day opening check on POS Invoice; tax, payment, stock and Sales Invoice validations remain native. Existing configuration permissions are unchanged.

Deployment: reload only Restaurant Company Settings metadata and the Python web controller. Do not run general after_migrate/backfill for this adaptation. Activate only approved settings. To roll back, disable the flag; native outdated-opening validation resumes. No historical data restoration is needed.

Tests: run the dedicated unittest module with initialized Frappe and a read-only development transaction. No invoice is saved or submitted by these tests. Source targets v16's extend_doctype_class hook.
