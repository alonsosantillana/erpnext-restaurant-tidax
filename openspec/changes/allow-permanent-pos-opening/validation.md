# Validation 2026-11-02

Development v16: 19 unittest scenarios PASS using actual native POSInvoice/SalesInvoice classes and narrowly mocked opening queries. Native error messages confirmed for disabled/missing/duplicate states. Read-only transactions; no invoice saves/submissions. Metadata cache was cleared after isolating test mocks to avoid pollution of role-cache queries.

Actual development controller MRO: ExtendedPOSInvoice → PermanentPOSOpeningMixin → POSInvoice → SalesInvoice. Targeted Restaurant Company Settings reload completed. Two actual primary profiles each rejected their past opening under default-off and accepted it with in-memory opt-in; both persisted flags remain 0. Specialized financial/technical review accepted with no material blockers. No after_migrate, backfill, closing or historical mutation.

Production activation and real user save remain pending; do not interpret these tests as a submitted production invoice or browser UAT.
