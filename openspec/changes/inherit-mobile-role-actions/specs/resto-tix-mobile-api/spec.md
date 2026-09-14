## ADDED Requirements

### Requirement: Context exposes effective ERPNext capabilities
The mobile API SHALL derive operational capabilities from current ERPNext permissions and POS configuration.

#### Scenario: Waiter lacks payment permission
- **WHEN** the authenticated waiter lacks effective restaurant payment permission
- **THEN** `can_generate_invoice` and `can_pay` are false

#### Scenario: Waiter has configured payment permission
- **WHEN** the waiter has direct POS Invoice create permission or permitted POS-profile payment access
- **THEN** the context reports invoice generation capability without exposing unrelated role data

### Requirement: Pre-account uses existing protected print queue
The mobile API SHALL validate order scope, print/write permission, version and idempotency before requesting the existing pre-account print operation.

#### Scenario: Same request is retried
- **WHEN** a completed pre-account request is repeated with the same UUID and payload
- **THEN** the previous response is returned without queuing a second print

### Requirement: Invoice generation uses authoritative POS rules
The mobile API SHALL validate effective payment permission, configured POS options and order version before calling the existing invoice operation.

#### Scenario: Client supplies one configured payment method
- **WHEN** an authorized user submits valid billing options
- **THEN** ERPNext calculates the payable amount and creates at most one invoice for the UUID

#### Scenario: Client supplies an unconfigured payment method
- **WHEN** the payment method is not enabled in the active POS Profile
- **THEN** the API rejects the request without creating an invoice

### Requirement: Quantity corrections remain limited to unsent items
The existing quantity mutation SHALL continue to accept only positive whole quantities for an unsent line.

#### Scenario: Sent item is decreased
- **WHEN** a client requests a new quantity for an item already sent to production
- **THEN** ERPNext rejects the mutation and preserves the order
