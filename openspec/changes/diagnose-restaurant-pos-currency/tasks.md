# Tasks

## Specification

- [x] Inspect both runtime call sites and existing currency tests.
- [x] Validate this OpenSpec change with Node 20.

## Implementation

- [x] Add bounded mismatch diagnostics with distinct stage labels.
- [x] Add focused tests for mismatch detail and unchanged success behavior.

## Verification

- [x] Run focused tests and diff checks.
- [x] Record branch, deployment requirements and the live retry still needed.

## Results

- Branch: `fix/restaurant-pos-currency-diagnostic` in an isolated worktree.
- OpenSpec validation: passed with Node 20.
- Three focused unit tests, Python compilation and `git diff --check`: passed.
- `ruff` is not installed in the bench environment.
