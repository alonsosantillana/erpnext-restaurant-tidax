## ADDED Requirements

### Requirement: Tips are separate from the taxable restaurant sale

The system SHALL record a voluntary tip independently from the Table Order and POS
Invoice payable amount.

#### Scenario: Invoice with a tip

- **WHEN** a cashier pays an order with a positive tip
- **THEN** the POS Invoice payments equal only the invoice payable amount
- **AND** the tip does not change invoice items, taxes, discounts, grand total, or the
  Nubefact payload
- **AND** the payment dialog shows the consumption, tip, and total collected separately

### Requirement: Company-isolated tip accounting

Each enabled Company SHALL configure a liability account for tips and SHALL collect a
tip through a cash or bank account belonging to that Company.

#### Scenario: Valid tip collection

- **WHEN** a paid order includes a tip and an allowed collection mode
- **THEN** the system creates one Restaurant Tip linked to the order and POS Invoice
- **AND** it debits the collection account and credits the configured tip payable account
- **AND** the record identifies the Company and waiter

#### Scenario: Invalid company account

- **WHEN** a tip account or payment account belongs to another Company
- **THEN** the server rejects the tip before creating the POS Invoice

### Requirement: Tip lifecycle follows the fiscal document

The system SHALL preserve an auditable relationship between a tip and its POS Invoice.

#### Scenario: POS Invoice cancellation

- **WHEN** a submitted POS Invoice with a collected tip is cancelled
- **THEN** the tip collection journal entry is cancelled
- **AND** the Restaurant Tip is marked Cancelled
- **AND** cancelled tips are excluded from operational totals

### Requirement: Tip reports are company isolated

Tip and closing reports SHALL read Restaurant Tip records and enforce the selected
Company and date range.

#### Scenario: Cashier views tip totals

- **WHEN** a user restricted to Company A opens the tip report
- **THEN** only tips for Company A are returned
- **AND** Company B tips are not disclosed
