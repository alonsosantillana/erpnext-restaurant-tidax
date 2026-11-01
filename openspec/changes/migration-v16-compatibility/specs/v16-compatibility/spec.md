## ADDED Requirements

### Requirement: Preserve contracts and restrictions under v16
The application SHALL resolve v16 framework APIs without bypassing existing authorization or changing business calculations.

#### Scenario: Native interface changed
- **WHEN** an existing read-only endpoint is invoked through its v16 interface
- **THEN** its expected response shape and existing access restrictions are preserved

#### Scenario: Access denied
- **WHEN** an existing scope check denies access
- **THEN** adapting an API name or neutral permission return MUST NOT grant that access

### Requirement: Isolated verification
The compatibility change SHALL be checked without modifying operational data or invoking external integrations.

#### Scenario: Pure verification
- **WHEN** compatibility tests run
- **THEN** only test doubles are called and no live business documents are written
