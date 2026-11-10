## ADDED Requirements

### Requirement: Native adapter rollout SHALL remain code-only
Installing the reviewed adapter SHALL not change data, permissions, configured
prices/taxes, schema, native authentication or core apps.

#### Scenario: Existing site receives reviewed adapter
- **WHEN** the clean native checkout is aligned to its approved pin
- **THEN** offline native and paired checks SHALL verify read-only behavior
- **AND** no order or invoice SHALL be created by the rollout
