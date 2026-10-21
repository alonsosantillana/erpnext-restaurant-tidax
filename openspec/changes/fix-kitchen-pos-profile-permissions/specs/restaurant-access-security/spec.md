## ADDED Requirements

### Requirement: Kitchen role can consult POS Profile

The operational-role installer SHALL grant resto_cocina read and select permission
on POS Profile at permlevel 0 without an owner-only restriction.

#### Scenario: Kitchen rule missing after installation

- **WHEN** operational permissions are synchronized and the kitchen POS Profile rule is absent
- **THEN** the rule is created with read and select
- **AND** the new mapping does not grant create, write, submit, cancel or delete
- **AND** it does not grant kitchen access to cash-session or invoice documents

#### Scenario: Existing kitchen rule is incomplete

- **WHEN** an existing kitchen POS Profile rule lacks read or select
- **THEN** the missing permission is enabled
- **AND** existing customized permissions are preserved

#### Scenario: Repeat install or migration synchronization

- **WHEN** the operational-role synchronizer runs again with both bits already granted
- **THEN** it does not duplicate the rule or unnecessarily update its permissions
- **AND** existing Company and room restrictions continue to apply
