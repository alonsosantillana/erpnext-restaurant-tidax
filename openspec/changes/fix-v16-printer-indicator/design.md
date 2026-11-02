## Sources and boundaries
Inspected installed Frappe16.54.0/ERPNext16.53.0 source: app_ready remains; page-change follows active-container selection; standard-items-section is the page header action host. Consulted Restaurant Management's existing local Graphify and verified actual source; Silent Print has no prepared graph. Read-only integration/QA specialist confirmed the missing anchor, single-target insertion, SVG coloring and lifecycle separation.

## Architecture
Modify only restaurant_management/public/js/restaurant_print_indicator.js, related tests and documentation. Select the first legacy navbar anchor when present; otherwise select the first header host under frappe.container.page, with a visible sidebar standard-items fallback if the header is unavailable. Move the same retained node on page-change; do not clone across hidden/cached pages. No MutationObserver/global DOM polling; keep existing timers and bootstrap guards. Each independently deployable app owns its small mounting adapter, avoiding a new mandatory cross-app runtime helper or asset-order dependency.

Render the printer SVG with explicit currentColor stroke and no fill, preserving grey/amber/green/red. The legacy action remains an explicit click registering the master tab; the restaurant link retains console URL, new tab and page-cache clearing. Mounting never calls activation, changes a master tab, reconnects or submits a job. Restaurant indicator suppresses only an already authorized legacy control, regardless of load order; losing assignment restores that control without granting access. Keep the last read error visibly red through navigation.

## Impact
No DocType, fixture, patch, API, backend permission, route, migration, report, invoice or business-state changes. App include paths stay unchanged. Deployment of static assets and actual site/browser/HWB acceptance remain separate, not authorized by source implementation.

## Validation
Offline DOM/RPC fixtures execute actual scripts with native v16/v15-shaped hosts, no account/DB/site initialization. Cover hidden cached pages, late header, A/B/A navigation, duplicate initialization, missing assignment/print-user, both load orders, state colors, restored legacy, fetch error, one click effect, no mounting RPC/WS effects and no FontAwesome. Re-run existing console/transport regressions when supported. Use an existing local browser if available; do not install dependencies or open ERP/HWB.

## Rollback and delivery
Independent fix/v16-printer-indicator branch from version-16 in each app. Revert only each UI commit if necessary. No data rollback. Commit locally and report publication/merge/deployment separately; user production restriction remains in force. Review the paired diff before closure.
