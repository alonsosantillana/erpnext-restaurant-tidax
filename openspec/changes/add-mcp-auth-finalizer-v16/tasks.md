## Preparation

- [x] Confirm v16 native authentication sequence and existing PedidosYa hook behavior.
- [x] Review the TIX preflight blocker and independent source architecture findings.
- [x] Consult the existing local graph and verify links against actual source.
- [x] Define optional bridge, paired responsibilities, tests, risks and reversal.
- [x] Validate this OpenSpec and the paired TIX proposal strictly.
- [x] Obtain independent paired-proposal review with no material coherence issues;
  keep implemented-code/security review pending.
- [x] Run the unchanged v16 auth baseline with blocked networking; record its
  21 setup errors at the obsolete cleanup API in validation.md, not as passes.
- [x] Obtain explicit approval for isolated multiapp code and tests; no site rollout.

## Implementation After Approval

- [x] Add the separate optional native hook and non-whitelisted bridge.
- [x] Retain standalone Restaurant behavior without TIX/callbacks.
- [x] Adapt native-auth hook maps/context cleanup for v16 and run original PedidosYa regressions.
- [x] Run paired TIX v16 tests with fake identities, state transitions and dispatch spy.
- [x] Independently review ordering, error behavior, ordinary users and drift limits.
- [x] Record Restaurant 42 and combined 185-pass, zero-skip results and limits.
- [ ] Verify remote backups of both implementation branches.

## Separate Deployment Gates

- [ ] Recheck paired loaded source, effective hooks/callbacks and marker assignments.
- [ ] Complete private baseline/session/socket/job and required-read review.
- [ ] Obtain exact rollout, cache/process and marker approval.
- [ ] Certify approved live checks and obtain maintenance merge/deployment approval.

Implementation and offline results are recorded separately above and in
implementation-validation.md. No installed update, role activation or merge is
implied. Work in this change is exclusively v16.
