# Tasks

- [x] Review bench rules, native fixture, graph and source/maintenance branches.
- [x] Isolate a dedicated worktree from version-16 without installed edits.
- [x] Validate both app specifications before editing tests.
- [x] Replace private local storage access with public isolated cleanup.
- [x] Target moved constructor/read mocks without changing native arithmetic.
- [x] Verify caller context restoration after success and setup failure.
- [x] Run native quote and paired TIX regressions on v15 and v16.
- [x] Obtain independent review; record limits, rollback and source provenance.
- [x] Commit/push dedicated branches, leaving installed/main branches unchanged.
- [x] Resolve or explicitly accept the inclusive-tax monetary difference before
  declaring the v16 quote contract accepted.

Companion: TIX fix-v15-v16-approval-test-fixtures. Live site, package compatibility
declaration, merge, deployment and services are outside this test-only task.

## Verification Record (2026-11-06)
- Public Local iteration/release replaces the v15-private storage access.
  Restoration preserves attribute values/identities for serial synchronous
  tests, not backing-dictionary identity or concurrent context synchronization.
- NativePriceRow supports v15 positional and v16 named access including packing
  unit. Synthetic selection follows each helper's inspected general-price
  fallback contract; the native helper is not replaced with computed rates.
- JSON-derived metadata supplies table maps, computed-table filtering and valid
  columns. Constructor controller lookup follows BaseDocument's defining module.
  Explicit get_single_value supplies the same synthetic settings on both versions.
  Both the FX definition and its imported native-pricing alias are blocked.
- Three new isolation cases cover nested normal cleanup, body failure, mutable
  and None sentinels, and actual unittest.run cleanup after setUp failure.
- AST comparison confirms all 85 original self.assert* expressions across 31
  native cases remain intact. No expected number, tolerance or skip was changed.
- Combined focused runs with TIX: **53 passed on v15**; **51 passed and two
  assertion failures on v16**, zero errors. These combine 34 native/isolation,
  eight adapter and 11 approval cases, not a 53-case native-only suite.
- Remaining v16 failures are native/paired assertions of inclusive tax 38.13
  versus actual native 38.14 at unchanged total 250. Independent review found
  no fixture defect explaining it: v15 uses rounded net; v16 uses unrounded net.
  Existing assertions remain a visible monetary-acceptance blocker pending a
  user decision, not a reason to patch production arithmetic or weaken tests.
- No live site, configuration, network, real mutation, regional tax override or
  provider was exercised. Core and installed checkouts remain unchanged. This
  is offline fixture implementation, not fiscal or installed-site certification.
- Source backup verified remotely: `4f95170` on
  `fix/quote-v15-v16-test-fixtures`; companion TIX `e6da6a0` on
  `fix/mcp-v15-v16-test-fixtures`. Installed branch remains at `9466ba8`;
  native version-16 remains at `c96d967`. No merge or deployment performed.
- Companion TIX full v15 discovery passed in one invocation with this native
  worktree explicitly selected: **2,174 cases, 2,072 passed, 102 skipped, zero
  failures/errors**. The 34 native/isolation cases are covered separately in the
  focused 53-case record, not added twice to full-discovery totals.
- Both new OpenSpec changes pass strict validation. The edited sources compile
  on Python 3.14; v15 focused runtime is Python 3.12. Documentation links and
  git diff --check pass. Temp artifacts stay outside Git. Existing monetary
  assertions and the visible v16 difference are retained pending acceptance.

## Accepted Expectation Follow-up
The user subsequently accepted each native major's exact result. The dedicated
change [accept-native-inclusive-tax-test-matrix](../accept-native-inclusive-tax-test-matrix/tasks.md)
changes only the native/paired inclusive tax expectation: 38.13 on v15 and 38.14
on v16, both at total 250. All 55 focused cases now pass on both inspected
matrices. Prior assertion-preservation and failure records above describe the
fixture-port phase before that explicit acceptance; production math, rates,
precision and all other expected monetary values remain unchanged.
