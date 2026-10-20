# Validation

- Branch: fix/client-script-name-migration, based on clean master e601930.
- Main branch confirmed through upstream/HEAD -> upstream/master.
- Before the fix, two new-script tests reached the actual Frappe Prompt naming
  check and raised ValidationError; the existing-script cases passed.
- After the fix, all four Client Script regressions and five existing company
  settings migration tests passed (9 total).
- Tests ran directly with unittest, storage and translation mocked, without site
  initialization, ERPNext test fixtures, live database writes, or network calls.
- Strict OpenSpec validation passed before the source edit and after implementation.
  The default Node 18 cannot parse this OpenSpec dependency; the already installed
  Node 22.23.1 was used without changing environment configuration or dependencies.
- git diff --check passed. The production diff is two added lines in set_custom_scripts.
- No files deleted; added tests and the dedicated OpenSpec change only.
- Local Graphify relationships were read and verified against hooks.py and source.
  No graph regeneration, query logs, external providers or versioned graph artifacts.
- No functional scope deviations, migrations, restarts, schema changes, permission
  changes, or server deployment performed. Full migration on the affected server
  remains pending; retain the OpenSpec change until deployment is verified.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 /home/erpnext/frappe-bench/env/bin/python -B -m unittest \
  restaurant_management.setup.test_install \
  restaurant_management.patches.v15_0.test_migrate_restaurant_company_settings
/home/erpnext/.nvm/versions/node/v22.23.1/bin/node /home/erpnext/.local/bin/openspec \
  validate fix-client-script-name-migration --strict
git diff --check
```
