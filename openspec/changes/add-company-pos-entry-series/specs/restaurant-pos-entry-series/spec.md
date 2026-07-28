## ADDED Requirements

### Requirement: Company-specific POS opening and closing series

The system SHALL generate POS Opening Entry and POS Closing Entry names from the
restaurant configuration belonging to the persisted document Company.

#### Scenario: Opening series

- **WHEN** a user creates a POS Opening Entry for Company A
- **THEN** its name uses Company A opening series
- **AND** the counter is independent from Company B

#### Scenario: Closing series

- **WHEN** a closing entry is created from a Company A opening
- **THEN** its name uses Company A closing series
- **AND** Company, POS Profile and opening entry remain consistent

### Requirement: Server-authoritative series

The series shown in the form SHALL be informative and SHALL NOT permit a client to
select or submit a series belonging to another Company.

#### Scenario: Missing company configuration

- **WHEN** a new opening or closing is inserted for a Company without configured series
- **THEN** the server rejects the insertion with an explicit configuration error

#### Scenario: Cross-company context

- **WHEN** Company, POS Profile or linked opening refer to different companies
- **THEN** the server rejects the document before insertion

### Requirement: Historical stability

The migration SHALL populate missing configuration values but SHALL NOT rename
existing opening or closing entries.

#### Scenario: Existing entry

- **WHEN** the migration runs after POS entries already exist
- **THEN** their names remain unchanged
