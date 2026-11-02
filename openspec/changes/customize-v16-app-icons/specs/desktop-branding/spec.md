## ADDED Requirements

### Requirement: Local recognizable launcher icon
The app SHALL declare a self-contained SVG icon served from its own public assets for the existing v16 Apps entry, using the coherent corporate-inspired icon family.

#### Scenario: Apps loads the installed app
- **WHEN** the authorized user opens Apps with this app available
- **THEN** its logo URL resolves to the local SVG instead of the alphabetical fallback

#### Scenario: Asset inspection
- **WHEN** the SVG is parsed or fetched over HTTP
- **THEN** it has a square viewBox, a correct SVG MIME type and no script, external resource, event handler or embedded bitmap

### Requirement: Branding preserves navigation and data
The icon change SHALL preserve existing launcher destinations, permission callbacks, Dock values, official apps and business data, and SHALL be applied only to development.

#### Scenario: Scoped deployment or rollback
- **WHEN** branding is applied or reverted
- **THEN** only the app icon and logo declaration change while existing navigation and concurrent work remain intact
