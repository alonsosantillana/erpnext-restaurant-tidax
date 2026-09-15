## ADDED Requirements

### Requirement: ERP remains authoritative for mobile order management
The API SHALL re-evaluate company, POS Profile, document permissions, waiter restrictions and order version for every mutation.

#### Scenario: Authorized mutation
- **WHEN** a permitted waiter sends a current, idempotent request
- **THEN** the API delegates to the stable restaurant rules and returns authoritative data

#### Scenario: Unauthorized discount
- **WHEN** the POS Profile does not allow changing discounts
- **THEN** the API rejects the mutation

#### Scenario: Divide or transfer
- **WHEN** a waiter divides an account or transfers an order
- **THEN** the existing `TableOrder` domain method performs the operation after facade validation
