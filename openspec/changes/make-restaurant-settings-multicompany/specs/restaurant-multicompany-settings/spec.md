## ADDED Requirements

### Requirement: Company-specific restaurant configuration

The system SHALL maintain at most one restaurant configuration per Company and SHALL
resolve it from the persisted business document whenever an order context exists.

#### Scenario: Invoice uses order company

- **WHEN** a Table Order for Company A creates a POS Invoice
- **THEN** the system uses Company A restaurant series and formats
- **AND** it does not use configuration from Company B or the current user's changed default

#### Scenario: Missing configuration

- **WHEN** an enabled restaurant flow starts for a company without configuration
- **THEN** the server reports that the company must be configured
- **AND** it does not silently use fiscal series from another company

### Requirement: Company-isolated restaurant objects

Every Room, Table and Production Center SHALL belong to one Company. Child objects
SHALL inherit their room Company and cross-company relationships SHALL be rejected.

#### Scenario: Room list isolation

- **WHEN** a user opens Restaurant Manage with Company A active
- **THEN** only Company A rooms, tables, counters and production centers are returned

#### Scenario: Cross-company transfer

- **WHEN** an order from Company A is transferred to a table from Company B
- **THEN** the server rejects the transfer without changing either table or order

### Requirement: Reversible legacy migration

The system SHALL copy the legacy Single configuration to the default operational
Company without deleting legacy values or duplicating fiscal series across companies.

#### Scenario: Repeated migration

- **WHEN** the migration executes more than once
- **THEN** no duplicate company setting or child exception is created
- **AND** existing company-specific changes are preserved
