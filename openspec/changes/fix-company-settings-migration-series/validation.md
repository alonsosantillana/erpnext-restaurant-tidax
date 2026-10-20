# Validation

## Automated checks

- Database-free unittest module:
  `restaurant_management.patches.v15_0.test_migrate_restaurant_company_settings`.
- Before the source correction: four tests reproduced MandatoryError at insert;
  the existing-settings early-return test passed.
- After the correction: all five tests passed, exercising the actual series validator.
- Covered all five generated series, existing-record skip, preconfigured series,
  cross-company POS profile filtering and exception-row preservation.
- Python compilation and `git diff --check` passed.
- OpenSpec strict validation passed using Node.js 20.20.2 before implementation.
- Graphify code-only extraction refreshed the ignored local graph:
  3121 nodes, 4772 edges, 357 communities. No generated graph artifacts are versioned.

## Scope and deployment status

Prepared on `fix/company-settings-migration-series`, based on `master`.
No migration, patch execution, service restart or live database writes were performed.
The affected remote server has not been accessed or migrated in this task.

After the reviewed correction is published and deployed, run from the target bench:

```bash
bench --site resto.v1.tidax.pe migrate
bench --site resto.v1.tidax.pe clear-cache
```

The operator should verify that migration completes and the company settings have
series based on their own company abbreviation. A failed Frappe patch is retried on
the next migrate; no manual Patch Log update or validation bypass is needed.

The full remote migration remains pending; these isolated tests do not establish that
unrelated subsequent patches will succeed on that server's data.
