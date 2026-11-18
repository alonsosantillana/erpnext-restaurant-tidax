# Tasks

- [x] Verify exact production app SHA and old/new native field equality.
- [x] Review Custom Field on_trash and native bypass deletion API.
- [x] Create dedicated development branch/worktree and this OpenSpec change.
- [x] Implement guarded metadata adoption and setup/hook integration.
- [x] Run pure guard/precedence/idempotency/no-DDL tests (18 passed).
- [x] Run authorized rollback-only development metadata trial with native ORM; verify invoice hashes/counts and complete metadata rollback preserved.
- [x] Validate OpenSpec and Git diff; prepare the tested feature for Git publication.
- [ ] Root verifies published feature SHA before production deployment.
- [ ] Production migration/resume and post-checks are performed only by the root operator under existing authorization.
