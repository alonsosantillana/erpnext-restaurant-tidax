## ADDED Requirements

### Requirement: Waiter reports support POS cash-session filters

Mozos vs Platos and Mozos Resumen SHALL provide optional Apertura POS and Cierre POS
filters in addition to their existing filters, without changing their displayed
columns.

#### Scenario: Filter by POS opening

- **WHEN** a user selects an Apertura POS
- **THEN** the report includes only submitted eligible POS invoices linked to that
  opening either directly or through their submitted closing

#### Scenario: Filter by POS closing

- **WHEN** a user selects a Cierre POS
- **THEN** the report includes only submitted eligible POS invoices referenced by that
  submitted closing

#### Scenario: Use both session filters

- **WHEN** a user selects both an opening and a closing
- **THEN** the report returns only invoices satisfying both filters
- **AND** item quantities and waiter totals are not duplicated

#### Scenario: Select a closing in the user interface

- **GIVEN** a company and optionally an opening are selected
- **WHEN** the user searches Cierre POS
- **THEN** only submitted closings for that company and selected opening are offered
