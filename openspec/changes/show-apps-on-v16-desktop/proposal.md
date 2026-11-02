## Why
Restaurant is installed in the development v16 site but has no Apps launcher hook or standard Dock. Users cannot discover its existing screens consistently.

## What Changes
- Add one native Apps entry and one app-owned standard Dock opening the existing Workspace `Restaurant Management` at `/desk/restaurant-management`.
- Preserve existing permissions, personal navigation, v16 upgrade fixes and all financial behavior.
- Apply only in the authorized development site; the other twelve installed custom apps have independent sibling changes with no runtime cross-dependency. Uninstalled apps remain uninstalled.

## Capabilities
### New Capabilities
- `desktop-navigation`: discover this installed app in Frappe v16 using its authorized existing destination.
### Modified Capabilities
None.

## Impact
Own hooks, a read-only permission helper and one app-root Dock JSON. No core, new roles, API, report, financial logic, site configuration, provider calls or production deployment. Native alphabetical launcher icon; no asset build required.

## Acceptance and Risk
Authorized System Users can discover and open the existing destination. Guest, Website User, absent app/target and denied users cannot obtain an app route. Existing user/site layers remain unchanged. Main risk: stale web hooks until the development reloader reloads; verify HTTP separately from CLI. Previously deferred business-logic defects remain outside this navigation change.
