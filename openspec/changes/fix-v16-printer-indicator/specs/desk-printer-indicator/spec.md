## ADDED Requirements
### Requirement: Version-aware visible print control
restaurant_management SHALL mount its authorized printer control in the current v16 Desk header or desktop sidebar fallback and preserve the v15 navbar placement when available.
#### Scenario: v16 page navigation
- **WHEN** the active page changes or its UI host becomes available after startup
- **THEN** the same SVG control moves to one visible host without duplicate IDs, handlers, bootstrap calls or WebSockets
#### Scenario: v15 compatibility
- **WHEN** the legacy combined navbar anchor exists
- **THEN** the control is mounted there with its original activation behavior
### Requirement: Preserve security and operational state
UI mounting SHALL NOT grant authorization, register a master tab, claim a station or submit printing. Existing backend guards and status colors SHALL remain unchanged.
#### Scenario: Unauthorized user
- **WHEN** no matching station or configured print-user permission is returned
- **THEN** the corresponding control is absent and no activation occurs
#### Scenario: Explicit activation
- **WHEN** an authorized user clicks the legacy control or restaurant link
- **THEN** only the original master-tab action or console navigation respectively occurs
### Requirement: Coordinate existing indicators
The restaurant station control SHALL supersede the legacy control regardless of initialization order and SHALL restore only an already authorized legacy control when station assignment disappears.
#### Scenario: Assignment changes
- **WHEN** a successful station refresh returns no assigned stations
- **THEN** the restaurant control is removed and the existing authorized legacy control may become visible
#### Scenario: Refresh failure
- **WHEN** an assigned station refresh fails
- **THEN** its error remains visible through navigation without initializing another receiver
### Requirement: Offline acceptance
Regression validation SHALL use synthetic DOM, RPC and WebSocket fixtures without site/provider/HWB connections or operational printing.
#### Scenario: UI-only test run
- **WHEN** startup, repeated refreshes, navigation and clicks are exercised
- **THEN** fixture counters prove that mounting adds no network/activation effects and no real jobs are submitted
