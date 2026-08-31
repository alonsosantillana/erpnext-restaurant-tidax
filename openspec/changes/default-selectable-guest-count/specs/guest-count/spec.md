## ADDED Requirements

### Requirement: Dine-in orders start with one guest

The system SHALL persist a newly created table order with one guest unless an
explicit valid guest count is supplied by an authorized flow.

#### Scenario: Order is created from a table

- **WHEN** an authorized user creates a new order from a restaurant table
- **THEN** the Table Order is saved with `guest_count = 1`
- **AND** the table people counter reflects that value

#### Scenario: External order is created

- **WHEN** a Delivery or Pickup order is created
- **THEN** the external-order flow MAY retain `guest_count = 0`

### Requirement: Guest count is selectable

The system SHALL provide a required guest-count selector for active dine-in
orders, derived from the table capacity and current order value.

#### Scenario: Normal table capacity

- **WHEN** the selector opens for a table with capacity N
- **THEN** it offers every integer from 1 through N
- **AND** it selects the order's current guest count

#### Scenario: Current value exceeds capacity

- **WHEN** an existing order has more guests than the current table capacity
- **THEN** its current value remains an available and selected option

#### Scenario: Guest count is saved

- **WHEN** the user selects and saves a positive guest count
- **THEN** the Table Order and the table people counter update without a page reload
