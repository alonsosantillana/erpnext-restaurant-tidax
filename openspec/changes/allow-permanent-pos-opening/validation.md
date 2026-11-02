# Validation 2026-11-02

Development v16: 19 unittest scenarios PASS using actual native POSInvoice/SalesInvoice classes and narrowly mocked opening queries. Native error messages confirmed for disabled/missing/duplicate states. Read-only transactions; no invoice saves/submissions. Metadata cache was cleared after isolating test mocks to avoid pollution of role-cache queries.

Actual development controller MRO: ExtendedPOSInvoice → PermanentPOSOpeningMixin → POSInvoice → SalesInvoice. Targeted Restaurant Company Settings reload completed. Two actual primary profiles each rejected their past opening under default-off and accepted it with in-memory opt-in; both persisted flags remain 0. Specialized financial/technical review accepted with no material blockers. No after_migrate, backfill, closing or historical mutation.

Production activation and real user save remain pending; do not interpret these tests as a submitted production invoice or browser UAT.

## Production deployment

The user explicitly approved integration/publication into version-16. Functional commit 975f01f was fast-forwarded, remotely verified and transported without modifications to production version-16. Targeted company-settings metadata reload only; no general migrate, after_migrate or backfill. One approved company/primary profile was enabled; the native Version audit contains only the flag's 0-to-1 business change and no table-row content changes. Parent save refreshes automatic child metadata; this was distinguished from business changes by the Version audit.

The actual POS Invoice controller passed opening validation using the existing older session. Counts and aggregate CRC fingerprints before/after remained identical for invoices, items, taxes, payments and GL entries; opening snapshots were identical. This integrity comparison does not replace a full accounting audit. No test invoice was saved or submitted. Web and two idle queue workers were reloaded; database, Redis, socketio and scheduler were not restarted. All 14 production login routes returned HTTP 200. The two other sites with this app kept the flag disabled and native outdated-opening rejection.

Browser/user confirmation of saving a new POS Invoice is pending. This is the only outstanding functional acceptance item. Rollback remains disabling the opt-in, with no historical data restoration.
