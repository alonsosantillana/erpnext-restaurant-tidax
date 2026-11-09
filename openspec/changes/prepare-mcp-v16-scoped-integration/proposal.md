# Scoped V16 MCP Integration Candidate

## Purpose And Approval

Prepare the owner-approved next step from the integration review: reproducible
backend tests and a Restaurant candidate without unrelated minimarket documents.
This prepares reviewable branches, not maintenance merges or deployment.

## Scope

Restaurant starts at version-16 c96d967 and selectively retains the MCP pilot
changes from c3d5342, without its five minimarket design documents. Add the
reviewed finalizer test and update the PedidosYa fixture for v16. TIX owns the
paired offline runner and its matching change.

## Exclusions And Risk

Risk: medium for new test tooling; the authentication code remains a reviewed,
security-sensitive dependency and must stay byte-identical. No native permission
acceptance, business action, site read/write, migration, service/cache operation,
core edit, channel activation, old restrict_read_account operator or principal
merge is authorized. No changes to DocTypes, grants, patches or data fixtures.

## Acceptance

Retain the 163 scoped backend cases and 72 current operator cases (235 distinct
cases; do not duplicate the five minimum-permission cases). Run only with explicit
candidate origins, offline guards before suite imports, exact case manifests and
zero skips. Add focused runner self-tests. Verify scope, OpenSpec, source equality,
independent review and remote backups. Residual native-rights risk stays pending.
