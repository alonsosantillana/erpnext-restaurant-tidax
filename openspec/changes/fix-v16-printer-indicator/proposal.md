## Why
The v16 Desk no longer provides the combined .navbar-brand.navbar-home element. The current printer indicator is created but never attached. Its FontAwesome glyph is also not a reliable v16 dependency.

## Scope
Restore the authorized printing indicator in restaurant_management, including page navigation, late UI creation and v15 fallback. The paired fix is independently specified in the other app. Both current maintenance branches are version-16; older v15 guidance is retained as backward compatibility, not as a reason to reject the explicitly authorized v16 correction.

## Exclusions and risk
Medium risk, UI-only. No server APIs, permissions, schemas, hooks, print payloads, WebSocket lifecycle, configuration, queue behavior, jobs, fiscal/accounting/stock data or core app changes. No production access, actual printing, deployment, migration, rebuild or restart.

## Acceptance
Visible SVG control in the active v16 page header (sidebar fallback on desktop), v15 navbar fallback, one node and one click handler after navigation, unchanged authorization and activation, restaurant precedence with legacy restoration, preserved status colors and no additional connections/RPCs from mounting.
