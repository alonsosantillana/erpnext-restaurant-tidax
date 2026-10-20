## Why

The legacy company-settings migration inserts Restaurant Company Settings while its
migration flag skips normal series validation. Later patches populate series, but
the insert already fails mandatory validation when upgrading directly to the current
schema with required order, expense and POS opening/closing series.

## Objective

Make the existing migration safe to retry by preparing valid company-specific series
before the settings document is inserted.

## What Changes

- Reuse validate_company_pos_series before inserting new migrated settings.
- Include reservation series through the same existing validation routine.
- Keep migration bypasses for unrelated operational settings and existing-record skip.
- Add database-free regression tests for fresh migration, repeat runs and isolation.

## Scope and Impact

- App: restaurant_management; existing post-model-sync migration patch only.
- DocType: Restaurant Company Settings; no schema, hooks, APIs, reports or fixtures change.
- Risk: migration logic; prepare and test locally without executing a site migration.
- No existing documents, numbering counters, invoices or product prices are rewritten.

## Acceptance Criteria

- A fresh settings insert receives all company-specific series before mandatory checks.
- Existing settings are not changed on retry.
- Legacy POS profile company filtering and exception rows are preserved.
- The normal series validator is used and mandatory checks remain enabled.

## Exclusions

No production migration, accounting changes, schema changes or remote-server access.
