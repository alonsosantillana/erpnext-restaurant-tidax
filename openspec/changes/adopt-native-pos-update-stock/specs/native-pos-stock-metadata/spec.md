## ADDED Requirements

### Requirement: Adopt the standard stock flag without invoice mutation
The application SHALL use the native POS Invoice.update_stock Check field when present and SHALL remove only duplicate Custom Field metadata through the native bypass API. It SHALL preserve the physical column, stored invoice values and existing inventory policy.

#### Scenario: Legacy duplicate on a native core
- **WHEN** the native source/DocField and duplicate Custom Field are compatible Check fields and the column exists
- **THEN** snapshot metadata, preserve existing overrides/layouts, add missing presentation Property Setters and remove only duplicate Custom Field metadata before fixtures.

#### Scenario: Existing property override
- **WHEN** a Property Setter exists for a property
- **THEN** preserve it unchanged and do not replace it with app defaults.

#### Scenario: Incompatible state
- **WHEN** the standard field, duplicate type or column is incompatible/missing
- **THEN** fail before any metadata mutation.

#### Scenario: Repeated migration or setup
- **WHEN** adoption has already completed
- **THEN** do not recreate the duplicate or add duplicate setters.

#### Scenario: Legacy core without a standard field
- **WHEN** the ERP source contains no native field
- **THEN** leave the existing Custom Field setup path unchanged.
