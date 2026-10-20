## ADDED Requirements

### Requirement: Compatible browser client before station startup

The print station SHALL verify the complete modern Silent Print client contract
before creating its printer or station controller.

#### Scenario: Legacy client is already present

- **WHEN** WebSocketPrinter exists but make_id or required lifecycle methods are absent
- **THEN** the station requests the modern Silent Print asset
- **AND** startup only proceeds after the complete contract is available

#### Scenario: Modern client is ready

- **WHEN** the complete modern client contract is already loaded
- **THEN** startup reuses it without an additional asset request
- **AND** the existing session client ID is retained when available

#### Scenario: Modern asset does not provide the required contract

- **WHEN** asset loading completes but the required contract is still incomplete
- **THEN** no station controller or printer connection is created
- **AND** an actionable error requests updating silent_print and reloading the page

#### Scenario: Asset loading fails

- **WHEN** the modern client asset request fails
- **THEN** startup reports the failure through the existing error display
- **AND** no incompatible printer instance is constructed
