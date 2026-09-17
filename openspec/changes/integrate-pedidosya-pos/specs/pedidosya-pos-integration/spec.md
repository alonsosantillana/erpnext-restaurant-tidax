## ADDED Requirements

### Requirement: Authenticated and idempotent dispatch

The system SHALL authenticate every PedidosYa dispatch before persistence and SHALL
produce exactly one inbox record and at most one restaurant order for each middleware
token.

#### Scenario: Valid first dispatch
- **WHEN** PedidosYa sends a valid signed order to an enabled remote vendor
- **THEN** the system persists it durably, returns a stable `remoteOrderId`, and queues processing

#### Scenario: Retried dispatch
- **WHEN** the same middleware token is delivered again
- **THEN** the system returns the original `remoteOrderId` without duplicating order, fulfillment or lines

#### Scenario: Invalid authentication
- **WHEN** the bearer token is missing, expired or has an invalid signature
- **THEN** the system rejects the request without persisting customer or order data

### Requirement: Asynchronous atomic import

The system SHALL validate the complete external order before atomically creating its
commercial and fulfillment documents under the configured integration user.

#### Scenario: Fully mapped order
- **WHEN** every external product code, quantity and price is valid
- **THEN** one Table Order and one fulfillment are created with all lines and source identifiers

#### Scenario: Unmapped product
- **WHEN** any payable product or topping lacks a valid mapping
- **THEN** no partial Table Order is created and the inbox records an actionable sanitized error

#### Scenario: Test order
- **WHEN** a dispatch has `test=true`
- **THEN** it is acknowledged and retained for certification without creating or sending kitchen lines

### Requirement: Platform logistics compatibility

The system SHALL distinguish PedidosYa rider delivery, vendor delivery and customer
pickup without inventing tables, customers, addresses or couriers.

#### Scenario: Platform rider hides address
- **WHEN** a delivery includes a rider pickup time and no customer address
- **THEN** the order is accepted as platform delivery and does not require an ERP Address

#### Scenario: Vendor delivery
- **WHEN** a delivery has no platform rider and includes a usable destination
- **THEN** its immutable destination snapshot is retained for operations

### Requirement: Controlled provider callbacks

The system SHALL send provider state updates only to HTTPS callback hosts authorized
by local configuration and SHALL keep restaurant processing independent from transient
provider outages.

#### Scenario: Order becomes ready
- **WHEN** all kitchen lines complete and a prepared callback exists
- **THEN** the system queues one authenticated preparation-completed notification

#### Scenario: Untrusted callback URL
- **WHEN** a payload supplies an HTTP URL or a host outside the allowlist
- **THEN** no outbound request is made and the integration records a security error

### Requirement: Auditable external cancellation

The system SHALL consume provider cancellations idempotently and preserve manual review
when local fiscal or logistics state prevents automatic cancellation.

#### Scenario: Cancellable order
- **WHEN** PedidosYa cancels an imported order before dispatch or invoicing
- **THEN** fulfillment becomes Cancelled once and records the external reason

#### Scenario: Order already dispatched or invoiced
- **WHEN** cancellation requires a refund, note or operational exception
- **THEN** the system preserves existing documents and marks the integration record for review
