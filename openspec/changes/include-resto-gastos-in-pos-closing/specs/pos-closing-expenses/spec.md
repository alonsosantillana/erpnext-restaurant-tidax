## ADDED Requirements

### Requirement: Net expected amount by payment method

The system SHALL calculate each expected balance as opening amount plus gross sales
collected through the payment method minus submitted expenses from the same opening
and payment method.

#### Scenario: Cash expense

- **GIVEN** an opening amount of S/ 100, gross sales of S/ 500, and submitted expenses of S/ 80 in cash
- **WHEN** the POS closing is prepared
- **THEN** the expected cash balance is S/ 520
- **AND** gross cash sales remain S/ 500

### Requirement: Expense isolation

The system SHALL exclude expenses belonging to another opening, Company, or payment method.

#### Scenario: Expense belongs to another opening

- **WHEN** a POS closing calculates its expense totals
- **THEN** an expense linked to a different POS Opening Entry is not included

### Requirement: Draft expenses block closing

The system SHALL NOT submit a POS closing while draft restaurant expenses exist for its opening.

#### Scenario: Draft expense exists

- **WHEN** the cashier submits a closing with a linked draft restaurant expense
- **THEN** submission is rejected with an actionable message

### Requirement: Submitted closing protects included expenses

The system SHALL NOT cancel a submitted expense already included in a submitted POS closing.

#### Scenario: Cancel included expense

- **WHEN** a user attempts to cancel an expense included in a submitted closing
- **THEN** cancellation is rejected

### Requirement: Reconciliation is idempotent

The system SHALL calculate reconciliation from opening, gross sales, and expenses
without subtracting an expense repeatedly during save or refresh.

#### Scenario: Closing is refreshed repeatedly

- **WHEN** the same draft closing is recalculated more than once
- **THEN** expected balances remain unchanged after the first calculation

### Requirement: Submitted summary belongs to the current closing

The system SHALL rebuild the submitted summary from the POS Closing Entry currently
displayed whenever the form refreshes.

#### Scenario: User navigates between submitted closings

- **GIVEN** two submitted closings have different totals, taxes, and payment rows
- **WHEN** the user navigates from the first closing to the second
- **THEN** the sales summary displays only values from the second closing
- **AND** a late response generated for the first closing cannot remain visible

### Requirement: Payment summary shows gross sales

The submitted payment summary SHALL show sales collected by payment method before
restaurant expenses are deducted.

#### Scenario: Cash sales and cash expense

- **GIVEN** cash sales of S/ 108 and cash expenses of S/ 30
- **WHEN** the submitted closing summary is displayed
- **THEN** the payment summary shows cash sales of S/ 108
- **AND** the reconciliation separately shows the S/ 30 expense and expected balance
