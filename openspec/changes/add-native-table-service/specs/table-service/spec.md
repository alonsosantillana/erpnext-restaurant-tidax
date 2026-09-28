# Table Service

## ADDED Requirements

### Requirement: Deliver completed dine-in dishes

The system SHALL allow an authorized waiter to mark selected Completed rows of
one active dine-in Table Order as Delivered. It SHALL reject missing, foreign,
duplicate, non-completed and stale rows without changing the order. It SHALL
preserve all other rows, prices, taxes, totals and document links, and SHALL
emit the native order update only after a successful transition.

#### Scenario: Deliver eligible dishes

- **WHEN** an authorized waiter serves selected Completed rows
- **THEN** only those rows become Delivered and the order totals are preserved

#### Scenario: Reject invalid selection

- **WHEN** a row is stale, foreign, duplicated or not Completed
- **THEN** no row is changed and no update event is emitted
