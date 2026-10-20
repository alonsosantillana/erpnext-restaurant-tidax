# Change: Name the restaurant room-permissions Client Script during migration

## Problem

The after_migrate hook calls set_custom_scripts(). On sites without the matching
POS Profile script, it inserts a new Client Script without a name. Frappe v15
uses Prompt naming for this DocType and raises `Please set the document name`,
preventing migration from completing. The after_install hook shares this code.

## Objective and Scope

Assign the stable name `Restaurant POS Profile Room Permissions` only when
creating this app's Client Script. Preserve the existing lookup, existing script
names, JavaScript, and legacy-script disabling behavior. Add database-free
regressions for creation, updating an existing script, and repeated execution.

## Exclusions

No changes to permissions, invoices, payments, external integrations, DocTypes,
fixtures, patches, core apps, or site configuration. No server deployment or
execution of install, migrate, or live data changes from this task.

## Impact and Risk

Low risk: this only supplies the missing identifier of a newly created setup
document. No accounting or tax behavior changes. The current validation and
lookup continue to apply. A conflicting document name remains a blocking error.

## Acceptance Criteria

- An absent room-permissions script is named before insert.
- An existing matching script retains its name and is saved rather than inserted.
- Repeated execution reuses the created script without creating duplicates.
- Legacy DeskForm scripts are still disabled and unrelated scripts are untouched.
- Focused tests run without a site, database writes, or network calls.

## Affected Components

- Spec: restaurant-installation.
- Source: restaurant_management/setup/install.py, set_custom_scripts().
- Tests: restaurant_management/setup/test_install.py.
- Existing hooks: after_install and after_migrate; their definitions do not change.
