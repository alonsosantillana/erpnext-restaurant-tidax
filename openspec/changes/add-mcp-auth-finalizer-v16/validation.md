# V16 Design And Baseline Evidence

Historical pre-implementation preparation. The source correction is now approved
and its executed results are in
[implementation-validation.md](implementation-validation.md). The failed baseline
below is retained as history, not as a claim that the fixture remains uncorrected.

## Status

2026-11-08 UTC. Proposal and documentation only, based on Restaurant version-16
c96d967. Paired implementation with TIX compose-mcp-reader-auth-v16 awaits explicit
multiapp approval. No production authenticator, native hook, test file, installed
checkout, role, permission, configuration, cache or service was modified.

Both paired OpenSpec proposals passed strict validation. Existing local Graphify
relations for PedidosYa were consulted without providers/query logs and checked
against native v16 source. The proposed bridge is not implemented or certified.
Independent review of both proposals found them technically ready for isolated
multiapp source approval without material coherence issues; it did not execute
tests, query the site or authorize operations.

## Existing Offline Regression Baseline

Runtime: Python 3.14.3, installed Frappe 16.55.2; Restaurant imported from the
isolated v16 source. A Python socket.connect patch rejected real network access.
No site initialization, real DB connection, queue operation or provider call.
The existing test fixture uses fake settings, synthetic JWTs and mocked receivers.

```text
restaurant_management.integrations.pedidosya.test_auth_hook
Ran 21 tests
FAILED (errors=21)
```

All cases stopped in setUp at:

```python
self.addCleanup(frappe.local.__release_local__)
```

The installed v16 Local does not expose that method. The native cleanup function
is frappe.utils.local.release_local(frappe.local). No test case reached a
successful result, and this run is not evidence of a live integration fault.
Do not bypass the failure with a production monkeypatch or report it as passed.

The proposed fixture update will use the v16 cleanup API and register cleanup
before failing setup can leak test-local state. It remains unimplemented and
requires the requested paired source approval. No baseline pass, bridge test,
new composition certification or deployment is claimed.

The companion unchanged TIX guard/policy/minimum-permission baseline passed 63
tests on the same v16 framework with real networking blocked. Those are existing
tests, not successful validation of this proposed bridge. No v15 test was run.

## Still Pending

Implementation approval, bridge code, fixture correction, original and paired
regression passes, independent implemented-code review and verified source
backups. Live rollout, effective-hook/loading review, private baseline,
account-marker operations and maintenance merges remain separate approvals.
