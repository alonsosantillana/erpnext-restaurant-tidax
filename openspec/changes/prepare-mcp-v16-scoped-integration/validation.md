# Scoped Candidate Preparation Evidence

## Scope And Source

Owner-approved preparation following the v16 integration review, dated 2026-11-09.
This is not a merge/deployment approval or native-permission risk acceptance.
Both apps use dedicated chore/mcp-v16-integration-candidate branches. Restaurant
records its own source, specification and validation; TIX owns the paired runner.

TIX starts at ce7de9c58ef3c46b8bef6e242dc8be6a048b1e9b, depending on its reviewed
pilot/activation changes. Restaurant starts at version-16
c96d9674ca448808debaa16afce6c3671d33f042. Remote maintenance bases matched their
recorded hashes before preparation. No principal branch was advanced.

The three runtime TIX files and two Restaurant files match the prior reviewed
blobs exactly. Restaurant selectively retains nine MCP source/documentation files
from c3d53427611dc949e8f2d03accce75aaa12757e7, plus the new preparation changes.
The minimarket commit 9466ba8 is not an ancestor; its five design documents are
absent from this candidate. Original branches and installed documentation remain.
README follow-up links are new documentation, not exact historical blob copies.

Both new OpenSpec changes passed strict validation before implementation. Local
Graphify queries were scoped separately per app, without regeneration/logging:
TIX's graph did not contain the new guards, Restaurant's contained PedidosYa but
not the new bridge. Direct source review supplied the current dependencies.

## Retained Test Sources

Four TIX backend modules were recovered from 9ed3c94810ebeb598302cbbb44305315a3ee7716
into mcp_server/backend_tests/, outside normal standalone MCP test discovery.
Restaurant fixtures were recovered from 5211f6eae12f86c6c292bc08829a5168fa30745c.
The paired import is mandatory, local v16 context is cleared before/after cases,
and DB doubles expose bounded method sets. No authorization assertion is relaxed.
Source ROOT checks now naturally refer to their own candidate, not patched /tmp.

AST inspection counted 235 methods across nine selected modules: 163 backend plus
72 current operator cases. The five minimum-permission cases are loaded once.
This static count is not a passing-test claim. The 22 old-operator cases and
restrict_read_account.py remain out of scope, retained only as historical evidence.

## Verified Offline Outcomes

Final runtime: Python 3.14.3, Frappe 16.55.2, ERPNext 16.54.0. The versioned TIX
runner executed all 235 explicit cases with zero failures, errors, skips,
expected failures or protected IO attempts. Its separate 25 stdlib-only self-tests
passed with no skips and no application imports or persistent audit hooks.
Reruns are repeat evidence, not additional unique test coverage.

Run from the TIX candidate root, using explicit absolute paths:

```bash
timeout 120s <bench>/env/bin/python -I -S -B \\
  mcp_server/deploy/verify_read_boundary_offline.py \\
  --bench <absolute-bench> --restaurant-root <absolute-restaurant-candidate> \\
  --dependencies <bench>/env/lib/python3.14/site-packages
<bench>/env/bin/python -I -S -B mcp_server/tests/test_read_boundary_offline_runner.py
```

The first two runs had 235 passing assertions but correctly failed qualification:
three psutil import-time CPU metadata reads and one urllib3 IPv6 socket capability
probe were blocked. The diagnostic rerun exposed only code-frame names/lines,
not arguments, file contents, identities or credentials. Only the exact public
/proc/stat read was then allowed; socket.has_ipv6 was temporarily set false
before imports to avoid the capability probe. No network access was permitted.

Independent review also found missing filesystem-metadata mutation events,
non-audited mkfifo/mknod APIs, symlinked import origins and private-directory
enumeration. These were fixed before the final run: audited metadata writes and
FD paths are checked, node creation uses destination-checked wrappers, lexical
source origins must equal resolved paths, and listdir/scandir/chdir are checked.
SQLite connections are also blocked. The reviewer confirmed those findings
closed in source; Main executed the tests. No reviewer claimed independent live
execution. Self-tests cover those regressions, caught IO, skipped/incomplete
results, duplicate IDs, source drift and isolated startup requirements.

All guards are local to the runner process and active before suite imports.
Only its private temporary directory is writable; raw dependency paths are
explicit and .pth startup is not processed. This is protection for reviewed
Python code, not a native-code/hostile-code OS sandbox. Operator fixtures remain
synthetic, including permissions and JWT data; no actual provider is contacted.

The full command and limits are documented in TIX's
mcp_server/docs/read-boundary-offline-tests.md. Final source and remote-reference
checks accompany delivery; installed source and maintenance refs stay unchanged.

## Verified Source Backups

Both source candidates were committed and pushed to their own upstreams under
chore/mcp-v16-integration-candidate. Actual ls-remote results matched:

- TIX: efc06cf045af97a27d4fbc6aad9f8ea9617669f4.
- Restaurant: be66a7a4aee121791b4b10934f8a6469de12c9af.

Maintenance references remained TIX 9d281ed0c9f7207f49e75d0055188a1d3eef79dc and
Restaurant c96d9674ca448808debaa16afce6c3671d33f042. Installed app checkouts were
clean and retained the original pilot pins. These hashes identify the qualified
source pair; later evidence-only commits do not change tested files. Their final
remote verification is part of delivery, not a maintenance merge.

## Limits And Recovery

No site, credentials, provider, business document, DB/Redis connection, services,
cache reset, migration, permission write or installed-source update is part of
this preparation. Existing installed pins remain TIX 41d8d21 and Restaurant
c1333a8. External MCP remains separately pinned; no reload is implied.

Native All-derived Item/Item Group rights remain a real warning; the separate
acceptance below does not remove grants or make the native profile least-privilege.
Synthetic tests do not certify prior sessions, sockets, jobs, all workers, POS or
universal read-only access. Following integration, any source-revert proposal must
be reviewed separately. Never remove the active marker or revert the installed
guard as an automatic rollback. Preserve original branches and concurrent changes.

## Owner-Accepted Risk And Maintenance Integration

On 2026-11-09 (America/Lima), the owner explicitly accepted the documented risk
of permissions inherited from All and authorized the paired maintenance merge.
This acceptance is bounded to the reviewed HTTP boundary: Item/Item Group still
inherit Export, Print, Email, Report and Share. Warnings stay visible. It is not
a native permissions remediation, a universal read-only certification, or an
authorization to deploy, remove the marker, change shared grants or enable actions.

Before merge, fresh upstream queries matched both recorded version-16 bases and
candidate tips. Clean isolated integration worktrees were used; no installed app
was switched. The exact source pair was revalidated from those worktrees:
235 paired cases passed with zero errors, failures, skips, expected failures or
protected IO attempts; the 25 runner self-tests also passed. Reruns add no new
unique coverage. OpenSpec and diff checks accompany the documentation closure.

Both fast-forward merges and normal pushes completed in dependency order:

1. Restaurant version-16: c96d9674ca448808debaa16afce6c3671d33f042 to
   af225df4b93d18a17f2215910f6bde67a31c39c1; ls-remote matched the new tip.
2. TIX version-16: 9d281ed0c9f7207f49e75d0055188a1d3eef79dc to
   0e3655b2620dcb585ecb1cf256baf7d10bb141e2; ls-remote matched the new tip.

This follow-up supersedes the earlier pending acceptance/merge gates, not their
historical findings. The subsequent commit only records this outcome and the
accepted risk; its incorporation and final remote hash are verified at delivery.
No authentication code, tests, native permissions or operational configuration
changes in that documentation closure. No force push or branch deletion is used.
The five minimarket documents remain outside Restaurant's integration ancestry.

Installed sources remain pinned to TIX 41d8d21 and Restaurant c1333a8, separate
from maintenance references. The external MCP runtime is not moved or reloaded.
No site operation, migration, restart, service/cache command or business write
was performed. Archival and deployment remain separate follow-ups.
