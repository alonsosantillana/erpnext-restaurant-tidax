# Design

In the existing offline test module, expected_inclusive_tax reads ERPNext's
major version and selects independent string literals from {15: 38.13, 16: 38.14}.
An unknown/malformed major raises an explicit AssertionError. It never calls the
engine, reads quote output or derives expected money from actual money.

The native inclusive test still requires exact total 250 and unchanged lines;
only its previously v15-only tax literal uses the accepted matrix. Companion
TIX imports this same helper for the paired assertion. Add tests exercising both
fixed oracles through patched version strings and rejection of unknown majors,
without loading a site or changing process-global versions beyond mock cleanup.

Keep all existing monetary inputs, precision, engine code and side-effect guards
unchanged. Version selection is only for this newly authorized expectation, not
for Local isolation or business execution. Verify on pinned temporary v15
sources/Python 3.12 and actual v16 sources/Python 3.14 with both app candidates
explicitly selected. No package installation, site initialization or real writes.

Data, schema, permissions, API, hooks, migrations and operational rollback: not
applicable. Revert the test commit to undo. The accepted test matrix is not a
declaration of external MCP package or fiscal/live-site compatibility.
