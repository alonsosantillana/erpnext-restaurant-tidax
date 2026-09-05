## ADDED Requirements

### Requirement: Production action color reflects the next step

The production dashboard SHALL visually distinguish completing a dish from starting it
without changing the state-transition behavior.

#### Scenario: Pending dish

- **GIVEN** a dish whose next status is `Processing`
- **WHEN** the kitchen dashboard renders the action
- **THEN** it displays `Iniciar plato` with the standard neutral appearance

#### Scenario: Dish in preparation

- **GIVEN** a dish whose next status is `Completed`
- **WHEN** the kitchen dashboard renders the action
- **THEN** it displays `Completar plato` with a green action appearance
- **AND** activating it executes the existing completion transition
