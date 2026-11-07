# Tasks

- [x] Record explicit acceptance; isolate from the native fixture candidate.
- [x] Validate both specifications before test edits.
- [x] Add fixed expectation/helper tests and update the native assertion.
- [x] Verify paired TIX assertion uses the same independent expectation.
- [x] Run focused and broader guarded regressions on both inspected versions.
- [x] Obtain independent review; update acceptance documentation and prior task.
- [x] Validate specs/diffs; commit and push the dedicated branch.

Do not alter actual tax computation, totals, rates, configuration, live data or
supported package ranges. No migration, service change, merge or deployment.

## Evidence
- Exact user criterion: native ERPNext v15 tax 38.13 and v16 tax 38.14 at total
  250. Native base 5296efd and companion TIX base 21155d0 remain separate from
  installed checkouts. Both specifications strictly validated before code edits.
- Helper returns only independent literals by major; tests check both reviewed
  values and unknown/future/malformed-major rejection. No computed response is
  used to construct the expectation, and equality remains exact.
- Focused combined suite: **55 passed on each version**, including 36 native/
  oracle/isolation cases, eight paired TIX cases and 11 approval cases. Broader
  backend selection: **939 passed on each version**. Zero failures/errors/skips;
  overlapping suites are not added together as unique coverage.
- Source/runtime pairs: Frappe 15.123.1 / ERPNext 15.109.0 / Python 3.12.3 and
  Frappe 16.54.0 / ERPNext 16.53.0 / Python 3.14.3. Existing runtimes and pinned
  temporary v15 core exports reused, with both candidate apps explicitly selected.
  Runner blocks site files/config, init/connect, network and subprocesses. No
  site, DB mutation, exchange-rate provider or package installation contacted.
- AST comparison confirms only the accepted native/paired inclusive assertions
  changed; every other original self.assert* expression remains intact. No
  production/native engine code, numeric input, precision, rate or guard changed.
- Independent static review found no issues; execution was by the primary agent,
  not the reviewer. Existing native graph lacks these recent test nodes and was
  not regenerated. Source inspection remained authoritative.
- Previous full v15 discovery belongs to the parent fixture candidate; this
  expectation delta is covered by the new focused/backend runs, not presented
  as a fresh full-suite or live fiscal/site certification.
- Source publication verified: native 5644083 on fix/quote-native-tax-expectations
  and companion TIX 68ed34b on fix/mcp-native-tax-expectations. Installed native
  checkout remains clean at 9466ba8, version-16 at c96d967. No merge/deployment.
