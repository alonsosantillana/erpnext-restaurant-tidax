## Why

Restaurant Manage reads POS Profile while initializing. The installer grants the
resto_cocina role Company read/select access but omits POS Profile, so a user with
Restaurant User and resto_cocina can fail startup with a POS Profile permission error.

## Objective

Give resto_cocina the minimum persistent POS Profile access needed by the restaurant.

## What Changes

- Add POS Profile read/select to dedicated kitchen permission rules.
- Include those rules in the existing operational permissions synchronizer.
- Apply through the existing after_install and after_migrate hooks.
- Test new-rule creation, repair and repeat runs with storage fully mocked.

## Scope and Risk

- App: restaurant_management; installer and installer tests.
- DocType affected at deployment: POS Profile Custom DocPerm for resto_cocina.
- No DocType schema, fixture, report, API or hook declaration changes.
- Permission changes are high-risk at deployment; the approved scope adds only
  read and select at permlevel 0, if_owner 0. Profile, Company and room assignments
  remain necessary and existing administrator customizations are preserved.
- No cash-session or invoice permission is added by this change.

## Acceptance Criteria

- Installation/migration creates or repairs the kitchen POS Profile read/select rule.
- Repeat synchronization does not duplicate it or unnecessarily rewrite permissions.
- No other kitchen privileges or other roles' rules are changed by the new mapping.

## Exclusions

No site migration, remote server changes, role assignments, room assignments or
blanket accounting permissions.
