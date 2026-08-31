## ADDED Requirements

### Requirement: Electronic invoices use a thermal 80 mm layout

The system SHALL render automated POS Invoice jobs with a layout whose physical
page width is 80 mm and whose printable content does not exceed 72 mm.

#### Scenario: Legacy invoice route is migrated

- **GIVEN** a company invoice route uses `Return POS Invoice`
- **WHEN** the migration runs
- **THEN** the route and company setting use `Restaurant POS Invoice 80mm`
- **AND** a custom invoice format is not overwritten

### Requirement: The thermal ticket preserves fiscal information

The ticket SHALL show the document identity, issuer and customer identity,
items, tax summary, discount, fiscal total, payments, SUNAT state and locally
rendered QR when those values exist.

#### Scenario: A collected tip exists

- **GIVEN** the POS Invoice has a collected Restaurant Tip
- **WHEN** the ticket is rendered
- **THEN** the tip is shown separately as a non-fiscal amount
- **AND** it is not added again to the fiscal total


### Requirement: Invoice routes support native ESC/POS transport

The system SHALL allow each print route to select PDF or ESC/POS transport.
Existing INVOICE and ACCOUNT routes SHALL migrate to ESC/POS while ORDER and
KITCHEN routes remain on PDF.

#### Scenario: An invoice job is rendered with ESC/POS

- **GIVEN** an INVOICE route uses ESC/POS
- **WHEN** its durable print job is rendered
- **THEN** the payload contains base64 RAW bytes instead of PDF content
- **AND** it includes fiscal identity, items, totals, payments, QR and cut
- **AND** requested copies are encoded as complete independent tickets

#### Scenario: A pre-account job is rendered with ESC/POS

- **GIVEN** an ACCOUNT route uses ESC/POS
- **WHEN** its durable print job is rendered
- **THEN** the payload contains a non-fiscal pre-account with table, dishes, discounts and total
- **AND** it does not include SUNAT QR or fiscal document identity

#### Scenario: A route uses PDF fallback

- **GIVEN** a print route uses PDF
- **WHEN** its job is rendered
- **THEN** the existing PDF payload and copy count are preserved
