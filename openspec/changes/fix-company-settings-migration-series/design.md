## Architecture

Call validate_company_pos_series(target) after copying legacy settings and child rows,
immediately before target.insert(ignore_permissions=True). This fills and validates
missing series using the existing Company abbreviation helpers, including reservation
series, while preserving any values already present on the target.

The existing restaurant_settings_migration flag remains set: changing its semantics
would enable unrelated operational validations on legacy data. The patch still exits
early for companies with an existing settings document. No new patch is required:
Frappe retries a failed patch that is not recorded as successfully completed.

## Affected Components

- restaurant_management/patches/v15_0/migrate_restaurant_company_settings.py
- restaurant_management/patches/v15_0/test_migrate_restaurant_company_settings.py
- Restaurant Company Settings creation during the existing post-model-sync patch.
- Reused pos_series.validate_company_pos_series; no changes to its implementation.
- No changes to DocTypes, hooks, APIs, reports, fixtures or core apps.

## Evidence

The local Graphify graph locates the migration, RestaurantSettingsMixin validation and
validate_company_pos_series. Direct code review confirms the migration flag returns
before series generation, mandatory validation still runs, and later series patches
cannot execute when insertion fails.

## Verification

Database-free unittest cases mock storage and exercise the real series validator.
An insert callback rejects missing required series to reproduce the original failure.
Cover generated series, existing-record retry, configured series preservation, and
legacy POS profile and exception handling. No bench test runner or live writes.

## Risks and Rollback

Company abbreviations remain required. Existing series ownership and format checks
still apply, so invalid configuration remains a blocking error. This intentionally
retains ordinary validation rather than ignoring mandatory fields.

Revert the patch call/import and tests to restore prior code. Preparing this change
requires no data rollback. Before deployment, back up the target site through the
operator's usual procedure; do not execute the migration from this development task.
