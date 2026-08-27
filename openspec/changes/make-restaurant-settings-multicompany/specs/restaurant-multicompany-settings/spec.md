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

#### Scenario: Inherited global company is not permitted

- **WHEN** a restaurant user has no personal Company value and the inherited global Company is outside its permissions
- **AND** the user has one globally applicable default Company permission
- **THEN** restaurant operations resolve the permitted default Company
- **AND** they do not use the inaccessible global Company

### Requirement: Company-isolated restaurant objects

Every Room, Table and Production Center SHALL belong to one Company. Child objects
SHALL inherit their room Company and cross-company relationships SHALL be rejected.

#### Scenario: Room list isolation

- **WHEN** a user opens Restaurant Manage with Company A active
- **THEN** only Company A rooms, tables, counters and production centers are returned

#### Scenario: Cross-company transfer

- **WHEN** an order from Company A is transferred to a table from Company B
- **THEN** the server rejects the transfer without changing either table or order

#### Scenario: Company without rooms

- **WHEN** an authorized restaurant administrator opens Restaurant Manage for a configured Company without rooms
- **THEN** the page identifies that no rooms exist for the active Company
- **AND** it offers an action to create the first room in that Company
- **AND** an operational user without configuration permission receives guidance instead of a blank page

### Requirement: Reversible legacy migration

The system SHALL copy the legacy Single configuration to the default operational
Company without deleting legacy values or duplicating fiscal series across companies.

#### Scenario: Repeated migration

- **WHEN** the migration executes more than once
- **THEN** no duplicate company setting or child exception is created
- **AND** existing company-specific changes are preserved

### Requirement: Company-specific restaurant order sequence

Each Company SHALL configure an independent Table Order naming series whose prefix makes the document name globally unique.

#### Scenario: Independent company correlatives

- **WHEN** Company A and Company B each create their first order in the same year
- **THEN** Company A receives `OR-{A}-.YYYY.-.#####` sequence number 1
- **AND** Company B receives `OR-{B}-.YYYY.-.#####` sequence number 1
- **AND** existing orders retain their original names

#### Scenario: Third company default

- **WHEN** restaurant settings are created for a third Company
- **THEN** its Table Order series defaults from its unique Company abbreviation
- **AND** the server rejects a series already assigned to another Company
