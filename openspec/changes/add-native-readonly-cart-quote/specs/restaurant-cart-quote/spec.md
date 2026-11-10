## ADDED Requirements

### Requirement: Native cart pricing SHALL reuse guarded order calculation
The app SHALL provide native cart quotations without persisting orders or invoices
and without changing existing full-order quotation contracts.

#### Scenario: Price-only pickup cart
- **WHEN** a valid customer and product quantities are supplied
- **THEN** the quote SHALL use configured native prices and taxes without contact data

#### Scenario: Delivery cart
- **WHEN** delivery has an owned readable address and configured fee item
- **THEN** the fee SHALL be calculated exactly once with configured charges

#### Scenario: Unsupported or forged input
- **WHEN** pricing overrides, unsupported rules or an unowned address are supplied
- **THEN** the quote SHALL fail closed and no write or provider call SHALL occur
