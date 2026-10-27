## Result — 2026-10-27

Implemented and validated exclusively in development (v15.local), branch `fix/pedidosya-callback-token-refresh`. No production or published-receiver connections, remote Git operations, merge, deployment, migrations, global scheduler activation or shared-queue consumption.

## Isolated tests

Regression tests were run before implementation and reproduced missing renewal and stale local-cache behavior. After implementation, all **70 standalone PedidosYa unit tests passed** (54 existing + 16 new methods, including subcases). They use installed RedisWrapper behavior with mocked network/storage; no bench run-tests or global ERPNext fixtures.

Coverage: cached/cold login; 401 renewal; second401 failure; failed renewed login; non401 and network failures without replay; same payload/timeouts and prepared empty body; stale local token removal; missing remote value; concurrent replacement at atomic invalidation; site/integration key isolation; cache failure; HTTPS validation before login; real service confirms only successful replay.

Strict OpenSpec validation and Python AST syntax checks passed. Integration/QA specialist reviewed source and final diff without blockers. Their cleanup finding was corrected: verification uses raw Redis GET so a connection failure cannot masquerade as successful token removal. The local dependency graph was consulted and verified against actual source; no graph artifacts are included.

## Real HTTPS/RQ development verification

Final evidence: `/tmp/pedidosya-token-refresh.ApEfi7GN/result.json`

SHA256: `dccf0353ccf5738f9062e6560d9242aa17a1d94451131af5b2de861602b081eb`

- Temporary loopback receiver from the development mock source, process-scoped certificate trust, strict HTTPS verification and synthetic credentials only.
- All four native callback contracts succeeded through the private RQ queue.
- Invalid token: **callback401 → login200 → callback204 in one job**, with automatic token replacement and notification confirmation.
- Expired token: the same bounded sequence in one job, without manual cache clearing.
- Bad credentials: login401 did not confirm the notification; restoring only synthetic credentials allowed recovery.
- Actual Redis Lua comparison preserved a newer token, cleared the stale local entry, and deleted only a matching rejected token.
- Five directed ScheduledJobType enqueue executions covered accepted/rejected 503→204, persistent503 and skipping confirmed callbacks. Thirteen distinct retained job records; this is not a count of all executions because recovery IDs are reused.
- Two successful full runs; an independent postflight verified both sets of eleven synthetic inboxes had no operational links or callback URLs, disabled fixture settings, absent raw token cache, empty private queues/no active private workers, unchanged operational counts and paused/disabled general scheduler.

Cleanup flags all true, errors empty: URLs removed, own token absent, fixture settings disabled, existing configuration/records unchanged, temporary receiver stopped, temporary resources removed and CA environment restored. Audit fixtures are deliberately retained; no operational order, fulfillment, invoice, payment, stock or accounting entry was created.

## Failure-path verification

Evidence: `/tmp/pedidosya-token-refresh-failure.3xEhUXrz/result.json`

SHA256: `884ffb457d2087008cb91c68e5a81782e6a6507172b1e80b85dac7b7879108c7`

Injected failure before fixture commit was observed as expected; all cleanup checks passed, including raw cache absence and unchanged existing data/configuration. No fixture inserts from that attempt were committed.

## Limits and handoff

The receiver is simulated, not PedidosYa's sandbox. Scheduler execution was targeted, not natural cron. Concurrent logins are not single-flight; the guarantee is that invalidating a rejected token cannot delete a newer value. Serialization follows the installed Frappe v15 RedisWrapper; revalidate when upgrading that dependency. Outgoing callback renewal does not add payment/accounting behavior.

Changes are for a local commit only. GitHub publication, principal-branch merge and any deployment require separate explicit authorization.

## Subsequent publication authorization — 2026-10-27

After completion of local commit `dd4ff666b91586856967d5199e91d6e151482c39`, the user explicitly requested integration into the principal branch and remote push. This authorizes merging into `master` and publishing to the existing `upstream` GitHub repository only. It does not authorize production access, deployment or restart. Before integration, `master` and `upstream/master` both resolved to `c498d693e0998f126934b5b73845879307c3bcf5`; all 70 isolated tests and strict OpenSpec validation passed again. No deployment workflows were present in the repository.
