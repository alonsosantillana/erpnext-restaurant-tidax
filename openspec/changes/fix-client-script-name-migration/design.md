# Design

## Architecture and Evidence

The existing after_install and after_migrate hooks call sync_app_metadata(), which
calls set_custom_scripts(). Graphify's local graph identifies these relationships;
hooks.py and setup/install.py confirm them. The Client Script JSON in local
Frappe declares autoname Prompt, and naming._prompt_autoname requires doc.name.

Keep the lookup by POS Profile, Form, and the get_room_permissions script marker.
After retrieving or creating the document, assign a deterministic name only if
the document is new. Keep the current insert/save choice and legacy disabling.
The generated script contains the same marker, so subsequent runs reuse it even
when an existing installation has a different script name.

## Files and Components

- Modify restaurant_management/setup/install.py with the new-document name.
- Add restaurant_management/setup/test_install.py with isolated unittest cases.
- No schema, DocType, hook definition, API, report, fixture, patch, role or
  permission changes. No new dependencies or changes to ovenube_peru.

## Verification

Mock all storage access and enforce the actual Frappe Prompt naming check during
the insert callback. Reproduce the absent-script failure before the source fix.
Verify new creation, repeated execution, existing-name preservation, and legacy
script disabling. Run unittest directly, without the Frappe/ERPNext test runner.
Validate OpenSpec and git diff whitespace. No live migration is part of this task.

## Risks and Rollback

The deterministic name might already belong to an unrelated script. Preserve the
ordinary duplicate-name error rather than overwriting an unrelated document.
The existing marker lookup and permission policy remain unchanged.

Revert the source change to restore the prior setup behavior. No site data is
changed by preparing or testing this fix; deployment must be coordinated by the
operator. A created Client Script can retain its name when code is rolled back.

## Graphify

The existing local graph was queried without generation or external services.
The fix changes an assignment, with no change to the production call structure;
regeneration is unnecessary for this patch. Generated artifacts stay unversioned.
