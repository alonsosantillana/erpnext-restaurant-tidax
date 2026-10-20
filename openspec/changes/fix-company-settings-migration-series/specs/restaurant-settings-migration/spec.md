## ADDED Requirements

### Requirement: Valid series before migrated settings insertion

The system SHALL initialize and validate company-specific document series before
inserting Restaurant Company Settings migrated from legacy Restaurant Settings.

#### Scenario: Upgrade from legacy settings to the current schema

- **WHEN** the company does not yet have Restaurant Company Settings
- **THEN** order, expense, POS opening, POS closing and reservation series are populated
- **AND** series are derived from the company's abbreviation through existing helpers
- **AND** mandatory validation remains enabled when inserting the document

#### Scenario: Repeated migration with existing settings

- **WHEN** Restaurant Company Settings already exists for the migration company
- **THEN** the migration does not replace its settings or naming series

#### Scenario: Legacy settings contain a POS profile for a different company

- **WHEN** a new settings document is migrated for a company
- **THEN** a legacy POS profile owned by another company is not copied
- **AND** legacy exception rows continue to be copied

#### Scenario: A target document already has a valid configured series

- **WHEN** series are validated before inserting the migrated document
- **THEN** the configured value is preserved
- **AND** missing series are filled from the company defaults
