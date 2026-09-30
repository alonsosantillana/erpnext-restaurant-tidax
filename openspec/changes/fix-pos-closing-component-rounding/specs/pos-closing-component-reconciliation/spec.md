## ADDED Requirements

### Requirement: Bounded component-rounding reconciliation

The system SHALL reconcile a POS Invoice component residual only when it does not
exceed the maximum aggregate error justified by the currency precision and the number
of non-zero source components.

#### Scenario: Accumulated rounding across many lines

- **WHEN** a restaurant POS Invoice has a residual within `ceil(N / 2)` currency units for `N` item and non-zero tax components
- **THEN** the residual is assigned to an eligible consolidated item from that same POS Invoice
- **AND** the consolidated components equal the POS Invoice grand total
- **AND** source taxes and the submitted POS Invoice remain unchanged

#### Scenario: Residual exceeds the calculated limit

- **WHEN** either the document-currency or base-currency residual exceeds its calculated tolerance
- **THEN** consolidation is rejected with the residual and allowed tolerance

### Requirement: Currency and return integrity

The system SHALL reconcile document and base currency independently and SHALL retain
the sign of return items.

#### Scenario: Base currency has a different residual

- **WHEN** document and base components produce different valid residuals
- **THEN** each residual is applied to its corresponding item amount and rate fields

#### Scenario: Return invoice residual

- **WHEN** a return POS Invoice has a valid negative residual
- **THEN** the selected consolidated item remains negative after reconciliation
