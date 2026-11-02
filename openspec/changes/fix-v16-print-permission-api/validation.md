# Validation 2026-11-02

26 tests PASS in initialized development v16 read-only transaction: 14 signature-aware permission regressions and 12 reused isolated print/electronic tests. The existing test functions were loaded into unittest.TestCase without Frappe fixture writers. Actual native callable tests confirm keyword compatibility; autospec enforces its signature for grant/deny/fallback branches. Guest session simulations use patch.dict. Queue, rendering and provider sinks are mocked: no real jobs, paper prints, invoices or external provider requests.

The exact production-code diff is two replacements of raise_exception=False with print_logs=False. No imports, access policy, fallback, route, idempotency, payload, DocType, role or database setting changed. Independent specialized review accepted the exact patch and QA without material blockers. git diff --check passes. Production deployment and normal user's physical printing remain pending.
