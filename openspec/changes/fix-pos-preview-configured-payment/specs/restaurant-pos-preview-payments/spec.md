## ADDED Requirements

### Requirement: Configured temporary payment
Invoice calculation without explicit payment SHALL use the single enabled default
payment method configured on the enabled POS Profile for the order company, without
persisting an invoice or recording a payment.

#### Scenario: Unrelated cash disabled
- **WHEN** the profile has a valid enabled default and a global cash method is disabled
- **THEN** calculation uses the profile default, preserves totals and validates normally

#### Scenario: Invalid profile default
- **WHEN** the default is missing, ambiguous or disabled, or the profile belongs to another company
- **THEN** calculation fails with an actionable profile configuration error and no fallback or settings change

### Requirement: Explicit payment preservation
Cashier payments SHALL be passed to invoice construction before the first invoice
validation, without replacing their names or amounts with temporary defaults.

#### Scenario: Mixed payment
- **WHEN** an authorized cashier supplies multiple payment methods
- **THEN** their amounts and names are used at first validation and at submission

#### Scenario: Explicit empty payment
- **WHEN** an explicit payment mapping is empty
- **THEN** construction fails without inventing a default charge

#### Scenario: Invalid explicit method or account
- **WHEN** native validation rejects a payment or its company account
- **THEN** the original validation error propagates without silently replacing the method
