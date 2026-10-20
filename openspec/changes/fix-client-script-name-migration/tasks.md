## 1. Analysis and Specification

- [x] 1.1 Confirm the failing call path, Prompt naming, and missing document name.
- [x] 1.2 Review Git, OpenSpec, local Graphify, source, hooks, and test safety rules.
- [x] 1.3 Create a dedicated branch from the clean master branch.
- [x] 1.4 Validate this specification before changing production source.

## 2. Implementation and Verification

- [x] 2.1 Reproduce the unnamed new-script failure with database-free tests.
- [x] 2.2 Assign a stable name only to new room-permissions Client Scripts.
- [x] 2.3 Verify creation, repeat execution, existing-name preservation and legacy disabling.
- [x] 2.4 Run focused regressions, OpenSpec validation, and git diff checks.
- [x] 2.5 Record results and review the final Git scope.

## 3. Deployment

- [ ] 3.1 Deploy the reviewed fix and retry migration on the affected server with operator authorization.

Deployment is outside the local preparation scope; no site migrations or data writes
are authorized by this change.
