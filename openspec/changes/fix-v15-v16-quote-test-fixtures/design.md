# Design

Snapshot public iteration of frappe.local; clear it with frappe.release_local,
which is used by both supported Frappe source lines. Register cleanup before
other setup work to clear synthetic state and restore every original attribute
and value identity on success or setup failure. Avoid private ContextVar names,
_Local__storage, version-number checks or a fake tax result. Add isolated
success/failure cleanup tests without loading a site.

Patch the constructor's controller lookup in the actual defining module of
BaseDocument, whose backward-compatible import remains available on v16.
If moved native read helpers require explicit fixture dependencies, patch only
their read/metadata entrypoints at the real lookup location. Do not replace the
POSInvoice class, its constructor, native price conversion or tax arithmetic.
Any newly exposed production incompatibility is a separate scope, not a reason
to weaken totals/assertions or change order_quote.py.

Only tests and docs change; schema, data, permissions, hooks, APIs, migrations,
tax settings and operational rollout are not applicable. Both version matrices
run with init/connect, network, configuration and mutation guards. Companion
TIX tests select this worktree explicitly, never the installed branch by accident.
Independent review checks arithmetic and guard preservation. Revert the dedicated
test commit to undo; no database or deployment reversal is needed.
