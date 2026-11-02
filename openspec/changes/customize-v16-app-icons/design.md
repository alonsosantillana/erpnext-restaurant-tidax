## Decision
Use a small original static SVG at `restaurant_management/public/images/app-icon-v1.svg`, referenced as `/assets/restaurant_management/images/app-icon-v1.svg` by the existing add_to_apps_screen entry. The asset has a square viewBox, rounded navy tile, a clear white functional glyph and cyan/amber accents based on existing corporate artwork. The corporate source palette was inspected; no third-party files or raster edits are needed.

## Scope and Access
Only the launcher image changes. Keep title, route, has_permission, helper source, Dock metadata and official apps intact. No API, DocType, fixture, patch, integration or transaction change. SVG contains no scripts, external links, fonts, animations or embedded bitmap data. Assets are non-sensitive public resources; existing native access remains authoritative.

## Branch and Deployment
Dedicated branch `feature/v16-app-icons-20261102` depends on `feature/v16-app-navigation-20261102`. Author in an isolated worktree. Apply only the reviewed local SVG and narrowly insert the logo key into the live hook after comparing its preimage; preserve unrelated hooks/WIP and live branch. Existing assets symlinks serve public files directly, so no build/migrate/restart or database import is required. Native cache clear only. No production or maintenance-branch merge.

## Validation
Strict OpenSpec before implementation; XML/viewBox/security checks and render a contact sheet at launcher size; AST must differ only by the intended logo key. HTTP all thirteen exact asset URLs, MIME, length and SHA256 must match their source. Native app_data must resolve the new logos while routes, visibility callbacks and Dock values remain equivalent. Browser visual acceptance is separate from native/static checks; if browser access is unavailable record that limitation.

## Rollback
Restore only the previous logo key (or remove it if absent) using the captured hook preimage; delete only the new icon file owned by this change and clear native caches. Preserve navigation, roles, Docks, existing public assets and all concurrent work. No site backup is needed for this reversible source-only change.
