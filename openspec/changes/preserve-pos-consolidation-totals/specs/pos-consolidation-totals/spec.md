## ADDED Requirements

### Requirement: Exact consolidated total

The restaurant POS consolidation SHALL produce a Sales Invoice whose currency total equals
the sum of the source POS Invoice currency totals.

#### Scenario: Separately rounded components lose one cent

- **GIVEN** a POS Invoice total is S/ 132.00
- **AND** its rounded net and tax components add to S/ 131.99
- **WHEN** the restaurant closing consolidates that invoice
- **THEN** the consolidated components add to S/ 132.00
- **AND** the consolidated Sales Invoice total remains S/ 132.00

### Requirement: No artificial change or write-off

The restaurant POS consolidation SHALL NOT represent a component-rounding residual as
customer change or as a write-off.

#### Scenario: Several invoices contain cent residuals

- **GIVEN** the source POS Invoices were fully paid without change
- **WHEN** their rounded component residuals are reconciled
- **THEN** `change_amount` is zero
- **AND** `write_off_amount` is zero
- **AND** the payment total equals the consolidated Sales Invoice total

### Requirement: Preserve source tax amounts

The restaurant POS consolidation SHALL preserve the tax amounts mapped from the submitted
POS Invoices.

#### Scenario: Residual is allocated

- **WHEN** a one-cent residual is allocated to a source invoice component
- **THEN** no consolidated tax row is increased or decreased by that residual
- **AND** the residual is assigned to an eligible sales item from the same POS Invoice

### Requirement: Reject non-rounding differences

The system SHALL reject a per-invoice component difference larger than one currency unit
of precision instead of silently reallocating it.

#### Scenario: Difference is greater than one cent in PEN

- **WHEN** the POS Invoice total differs from its net and tax components by more than S/ 0.01
- **THEN** consolidation is blocked with the affected POS Invoice and difference
