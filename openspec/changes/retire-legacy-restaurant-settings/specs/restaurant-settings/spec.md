## ADDED Requirements

### Requirement: Company settings are the sole runtime source

The system SHALL resolve restaurant configuration only from
`Restaurant Company Settings` for the relevant Company.

#### Scenario: Company has no configuration

- **WHEN** a restaurant flow runs for a Company without company settings
- **THEN** the system reports missing company configuration
- **AND** it does not reuse values from the legacy Single

### Requirement: Legacy settings are not operationally exposed

The operational Workspace SHALL link to `Restaurant Company Settings` and SHALL NOT
present legacy print-routing controls.

#### Scenario: User opens restaurant configuration

- **WHEN** an authorized user follows the restaurant Workspace configuration link
- **THEN** the company settings list opens
- **AND** legacy table-prefix fields are absent

### Requirement: Order printing uses company routes

An order print request SHALL use the `ORDER` route for the order Company and SHALL
remain optional.

#### Scenario: ORDER route is disabled

- **WHEN** a sent order belongs to a Company without an enabled `ORDER` route
- **THEN** the order remains sent successfully
- **AND** no legacy prefix-based print request is generated
