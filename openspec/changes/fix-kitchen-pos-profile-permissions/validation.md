# Validation

## Results

- `python -m unittest restaurant_management.setup.test_install -v`: 7 tests passed.
- Before the implementation, all three new kitchen tests failed because the
  POS Profile grant was missing; the four existing installer tests passed.
- After the implementation, creation, incomplete-rule repair, preservation of
  customized grants, repeat-run idempotence and adjacent installer tests passed.
- All storage and permission-writing operations were mocked; no site initialized.
- Python compilation and `git diff --check` passed.
- OpenSpec strict validation passed with Node.js 20 before source edits.
- Independent final review: no blocking findings. The only new mapping is
  POS Profile read/select for resto_cocina; Company read/select already existed.
- Graphify code-only extraction refreshed the ignored local graph:
  3151 nodes, 4806 edges, 348 communities. No generated graph files are versioned.

## Permission scope

The new grant enables level-0 POS Profile reading through normal Frappe permissions.
Applicable users determine operational profile selection, not a standalone
restriction on all document reads. Existing Company/User Permissions remain in
effect. The synchronizer adds missing bits and intentionally does not revoke
administrator-customized privileges or change assignments to users and rooms.

## Deployment status

Branch: `fix/kitchen-pos-profile-permissions`, based on `master`.
No live permission rows, users, rooms, profiles, accounting records or item prices
were modified. No migrate, cache-clear or service restart was performed.

After publishing and deploying the correction, run on the affected server:

```bash
bench --site resto.v1.tidax.pe migrate
bench --site resto.v1.tidax.pe clear-cache
```

Then sign in again as the kitchen user and verify Restaurant Manage startup.
Company default, operational POS profile and room assignments must still be
configured. Target-site migration and kitchen login remain unverified here.
