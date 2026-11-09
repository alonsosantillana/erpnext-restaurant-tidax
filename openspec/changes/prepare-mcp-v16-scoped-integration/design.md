# Design And Recovery

## Boundaries

Use isolated worktrees; never switch the installed apps. The new branch derives
from version-16, transferring only the nine MCP pilot files reviewed in c3d5342.
Their runtime blobs remain identical; existing minimarket branches are untouched.
Read the paired repository's matching change before acceptance.

## Offline Test Design

Recover four TIX modules from 9ed3c948 and two Restaurant fixtures from 5211f6ea.
Place the four Frappe-dependent modules in mcp_server/backend_tests/, outside
ordinary standalone MCP test discovery; minimum-permission/operator tests stay
in tests/. Remove the paired skip and require the explicit Restaurant source.
Tests derive roots from their own checkout, not temporary patching of ROOT.
The runner takes explicit bench and Restaurant roots; its TIX root comes from its
own file. Prepend these candidate roots and verify module source files, including
Frappe/ERPNext v16. Import only the explicit seven historical scoped modules and
two current operator modules; the five minimum-permission cases are counted once.
Keep the 22 old-operator cases separate rather than importing their dependency.

Before any application/suite import, block socket/DNS/network and subprocess
operations and private/site configuration reads. Before suite loading, also block
Frappe site initialization/connection and native DB/Redis command execution.
Use only process-local guards, temporary synthetic files, mocks and memory.
Fail on import-origin mismatch, missing suites, count drift, any skip, failed test
or attempted protected IO, including exceptions caught inside tested code.
No private configuration, credentials or HTTP target is an input to this runner.
The runner is test tooling, not an OS sandbox against hostile Python.

## Validation And Rollback

Use the existing bench Python and Node/OpenSpec executables; install nothing.
Validate specifications before implementation, run the focused runner and its
self-tests, inspect exact diffs and verify remote hashes. Record actual results,
not expected counts as passing evidence. Native permission risk remains visible.
The installed source pair, external MCP pin, roles and grants remain unchanged.
No database migration, tax, permissions, realtime or business-data rollback applies.
Recovery is to abandon the isolated candidates while preserving branches; do not
remove an active marker, revert installed guard code, delete user work or alter
shared rights. A later paired merge/deployment requires its separate approval.
