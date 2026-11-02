## Context and Decision
Use the pinned v16 Apps + Dock contract, not deprecated Desktop Icon or archived Workspace Sidebar. Target: Workspace `Restaurant Management`, route `/desk/restaurant-management`. Reuse native target permissions, with no grants. Eight sibling apps use Workspace entries; five utility apps use URLs to existing DocTypes. No Sidebar is created.

## Files and Permissions
`restaurant_management/hooks.py`: add_to_apps_screen. `restaurant_management/desktop_navigation.py`: boolean callback, System User and installed-app gates; Workspace entries use native get_app_entry_set; DocType entries require an existing unblocked module and native read permission. `restaurant_management/dock/restaurant_management/restaurant_management.json`: standard Dock, empty user/mount_on, one entry. README documents the route. No hooks are called during boot that write metadata.

## Activation and Migration
Native future v16 installs/migrations import app-root Dock JSON. Current development application uses the native exact-file importer for the thirteen manifested Docks, collision checks, transaction rollback on failure and restoration of in_import. No full migration, restart, installation, fixture sync or after_migrate hook. Apply twice to prove idempotence. Author in an isolated feature worktree and deploy only the three reviewed runtime files into the existing development checkout, preserving concurrent WIP/branches. No production changes.

## Alternatives and Scope
Workspace alone is insufficient for Apps. Desktop Icon seeding and global migration are broader than necessary. Custom sidebar, new permissions, external logos and new functional screens are excluded. APIs, reports, patches and financial data migration: not applicable.

## Validation
Strict OpenSpec before code; syntax/JSON/contract tests; negative permission tests; native boot and targets; HTTP process reload and browser click where authenticated session permits; unchanged personal navigation and financial invariants. Specialized architecture review: nav16_specialist_recommendation_20261102.md. Consulted existing README/OpenSpec and graph where present, then verified pinned source.

## Rollback
Restore only the three deployed runtime files from their recorded preimage and remove only newly created standard app-owned Dock documents listed in the manifest. Preserve official Docks, user/site layers, roles and Workspaces. Clear native caches. Do not revert unrelated work or use a site backup.
