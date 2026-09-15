# Resto TIX ready dish count

## ADDED Requirements

### Requirement: Aggregate ready dishes per accessible table

The ERPNext mobile facade SHALL expose `ready_items_count` in each accessible active-order summary.

#### Scenario: Mixed kitchen states

- **GIVEN** an accessible active order has item quantities in `Completed` and other states
- **WHEN** `get_tables` is requested
- **THEN** `ready_items_count` equals only the sum of quantities in `Completed`

#### Scenario: No ready dishes

- **GIVEN** an accessible active order has no items in `Completed`
- **WHEN** `get_tables` is requested
- **THEN** `ready_items_count` is zero

