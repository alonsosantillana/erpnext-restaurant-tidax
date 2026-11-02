# Validation 2026-11-02

26 tests PASS in initialized development v16 read-only transaction: 14 signature-aware permission regressions and 12 reused isolated print/electronic tests. The existing test functions were loaded into unittest.TestCase without Frappe fixture writers. Actual native callable tests confirm keyword compatibility; autospec enforces its signature for grant/deny/fallback branches. Guest session simulations use patch.dict. Queue, rendering and provider sinks are mocked: no real jobs, paper prints, invoices or external provider requests.

The exact production-code diff is two replacements of raise_exception=False with print_logs=False. No imports, access policy, fallback, route, idempotency, payload, DocType, role or database setting changed. Independent specialized review accepted the exact patch and QA without material blockers. git diff --check passes. Production deployment and normal user's physical printing remain pending.

## Authorized release and production verification

The user explicitly approved integration/publication in version-16 and production deployment. Functional commit e4aab93 was fast-forwarded and remotely verified, then deployed byte-identically to the production version-16 checkout. The web process and two idle queue workers were reloaded. No migrate, build, site backup, metadata/configuration/role change or historical mutation was performed.

In a fresh production process, the actual native print endpoint passed permission checks under the real source invoice owner's user and reached the unchanged manual-print queue contract. Only enqueue_print was substituted so no real print job, duplicate ticket or provider request was generated. The electronic access gate passed under the same user, and Guest remained blocked before queueing. These checks ran in a read-only database transaction. The configured ESC/POS station remained enabled and active; all three installed restaurant sites returned HTTP 200 on login.

Normal-user physical print confirmation is pending; a successful isolated endpoint test does not prove paper output. The user was asked to refresh and click Print once. Source rollback remains reverting the dedicated functional commit and reloading the affected processes without replaying jobs or restoring business data.
