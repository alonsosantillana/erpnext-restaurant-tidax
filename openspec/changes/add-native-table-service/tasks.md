# Tasks

- [x] Add native waiter-authorized delivery procedure with concurrency checks.
- [x] Test eligible delivery, other-order row, stale version/status, permissions,
      replay rejection and unaffected totals/rows.
- [x] Run focused tests and record results: 5 unit tests passed.
- [x] Verify against a test site after deployment, including idempotent MCP replay.

Live verification (reported by operator, 2026-09-28): a completed row was
delivered once; replay did not write again, and invalid rows were rejected.
