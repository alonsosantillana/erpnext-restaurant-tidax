## MODIFIED Requirements

### Requirement: Billing access distinguishes table and off-premise orders

The mobile POS invoice endpoint SHALL retain company, POS Profile and native
order permission checks. It SHALL allow a roomless, tableless Delivery or
Pickup order through the room gate only for an explicitly opted-in billing
operation. Other mobile operations SHALL keep their current room scope.

#### Scenario: Authorized off-premise billing

- **GIVEN** a Delivery or Pickup order without room or table in the active POS context
- **WHEN** the billing access validator is explicitly opted in
- **THEN** it checks native order permission without requiring a room

#### Scenario: Dine-in room remains restricted

- **GIVEN** a Dine In order in an unauthorized room
- **WHEN** any caller validates access, including billing
- **THEN** access is denied before invoice creation

#### Scenario: Unrelated mobile operation remains restricted

- **GIVEN** a roomless Delivery or Pickup order
- **WHEN** a caller does not opt into off-premise billing access
- **THEN** the existing room gate denies access

#### Scenario: Malformed off-premise order is denied

- **GIVEN** a Delivery or Pickup order carrying a room or table
- **WHEN** billing access is validated
- **THEN** access is denied before invoice creation
