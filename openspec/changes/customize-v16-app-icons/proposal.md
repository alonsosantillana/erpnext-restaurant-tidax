## Why
The authorized development Apps screen now lists Restaurant using the native alphabetical fallback. A recognizable functional icon improves discovery and consistent corporate presentation.

## What Changes
- Provide one original self-contained SVG in the app public images directory and declare its local URL in add_to_apps_screen.
- Use a coherent TIDAX-inspired navy/cyan/amber palette and a distinct functional glyph; this is an application icon, not a replacement third-party trademark.
- Apply only in development, preserving current launcher routes, permissions, Docks and concurrent work.

## Capabilities
### New Capabilities
- `desktop-branding`: local app-owned icon for the v16 launcher.
### Modified Capabilities
None.

## Impact
One SVG, one logo key in hooks, README and this change record. No core, permission, financial logic, metadata, build, migration, site configuration, external service or production change. Low operational risk: asset URL or stale boot cache; verify HTTP and native app_data. Rollback restores the logo preimage and removes only the newly added SVG.

## Dependency
This dedicated feature branch starts from the already validated navigation feature branch, which has not been merged into version-16. Integrate navigation before branding when preparing the release. Other apps have equivalent independent branding changes; no runtime cross-app dependency.
