# Development acceptance evidence — 2026-11-02

App: `restaurant_management`. Existing target: `Restaurant Management` at `/desk/restaurant-management`.

- Strict OpenSpec validated before functional implementation and revalidated for delivery.
- Specialized source review accepted all thirteen app contracts and native icons; independent permission tests passed 111 cases across the thirteen helpers. The application preflight separately passed 88 permission cases before deployment.
- Native app_data returned thirteen visible custom apps with nonempty routes/Docks for Administrator; Guest returned thirteen hidden apps with empty routes/Docks. Five existing enabled internal users were checked without changing roles; denied routes stayed hidden. No user identifiers were exported.
- Only the thirteen app-owned Dock JSON files were imported through the native exact-file importer. Two passes produced one standard Dock per app, with no duplicates. Existing official Docks, site/user navigation, Workspaces, roles, permission rows, installed apps and selected financial/inventory counts/GL aggregates matched their pre-application values.
- HTTP ping and unauthenticated login redirect returned HTTP 200. The operator confirmed visibility and supplied an authenticated screenshot showing all thirteen custom apps, including WMS ACC, in the development Apps screen.
- Automated browser control stopped because it could not establish Chrome's current URL. A proposed privileged internal QA session was rejected before execution; no such session was created. The operator's existing session provided visual acceptance instead.
- Individual app click journeys and business transactions were not re-executed for this navigation change. Existing targets and native access contracts were verified; no financial fixes, integration calls, new installations or production changes were made.
- Code was authored in isolated feature worktrees based on the existing version-16 source. Exactly hooks.py, desktop_navigation.py and the Dock JSON were deployed into development. Existing checkout branches and concurrent printing changes were preserved; READMEs/OpenSpec are maintained in the feature worktrees.
- Formatting corrections retain identical Python AST; runtime preimages and deployment manifest are retained outside the repos. Private site identifiers, business snapshots and credentials are excluded from publication.

Final commit/push is recorded separately after delivery. No maintenance-branch merge has occurred. Rollback is limited to these runtime preimages and the new standard Dock owned by this app, preserving user/site layers.

Source delivery: commit `aab2e51bee69e071e729f3769ece244890cab656` was pushed to `upstream` / `feature/v16-app-navigation-20261102` and its remote ref was verified. The final documentation commit records this evidence; maintenance branches and production remain unchanged.
