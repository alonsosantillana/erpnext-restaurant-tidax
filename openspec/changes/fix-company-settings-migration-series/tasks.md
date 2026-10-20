## 1. Preparation

- [x] 1.1 Verify patch ordering, mandatory fields and migration validation bypass.
- [x] 1.2 Consult Graphify and verify findings against source.
- [x] 1.3 Validate OpenSpec before source changes.

## 2. Implementation and Checks

- [x] 2.1 Initialize and validate company series before the legacy settings insert.
- [x] 2.2 Add regression tests without database writes.
- [x] 2.3 Run focused tests and static checks; record results.
- [x] 2.4 Refresh local Graphify artifacts and verify Git scope.

## 3. Deployment

- [ ] 3.1 Retry migrate on the affected server after deploying the reviewed fix.
