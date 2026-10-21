## Implementation

Define KITCHEN_PERMISSION_RULES with one entry: POS Profile: (read, select).
Add its resto_cocina mapping to permission_rules in set_operational_role_permissions.
Reuse the existing Frappe add_permission/update_permission_property flow, which
looks up permlevel 0 and if_owner 0, adds missing permissions, and clears metadata
cache. Existing after_install/after_migrate hooks already invoke this flow; no new
one-shot patch is necessary and existing installations are repaired on migration.

## Impact and Evidence

The local Graphify graph identifies set_operational_role_permissions and installer
tests. Direct source review confirms that kitchen is in OPERATIONAL_ROLES but has
no POS Profile grant, whereas cashier, production and reservation roles do.

Affected source: restaurant_management/setup/install.py and test_install.py.
Affected deployment data: Custom DocPerm, POS Profile, role resto_cocina.
No changes to APIs, business documents, DocTypes, fixtures, report access, user
assignments, or Company/room authorization code. Standard Frappe permissions remain
in effect. This scoped grant is not a complete audit of all existing role permissions.

## Verification

Use database-free unittest tests against the actual synchronizer with Frappe's
storage and permission writers mocked. Assert kitchen access is restricted to the
existing Company mapping and the new POS Profile read/select mapping, test missing
selection repair, preserve existing custom grants, and verify repeat runs create
no duplicate rules. Run existing installer tests to cover adjacent migration logic.
An independent permissions review is requested before completion.

## Deployment and Rollback

After publication and deployment, run migrate on the affected site to apply the
normal after_migrate synchronization, then refresh the user's session. Remote
migration and a live kitchen login are not performed in this development task.

Revert the new mapping to stop future grants. A code revert alone does not revoke
an already-created Custom DocPerm. If rollback is needed, remove only the kitchen
POS Profile rule or the newly added read/select bits through the role-permission
manager after checking pre-existing customizations; clear permissions cache.
No document or numbering data needs restoration.
