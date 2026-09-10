## ADDED Requirements

### Requirement: Mobile client reuses the restaurant order domain
The waiter mobile application SHALL use the existing restaurant backend as the authoritative source for permissions, orders, items, prices, taxes, production routing and totals, and SHALL NOT maintain an independent commercial database or calculation engine.

#### Scenario: Same order in web and mobile
- **WHEN** an authorized waiter opens the same active table order from the mobile client and Restaurant Manage
- **THEN** both clients receive the same persisted items, quantities, notes, preparation states and totals

### Requirement: Authorized restaurant scope
The mobile backend SHALL return and accept only Companies, POS Profiles, rooms and tables permitted to the authenticated user.

#### Scenario: Unauthorized room
- **WHEN** a waiter requests or mutates a table outside their permitted room
- **THEN** the server rejects the operation without returning order or customer details

### Requirement: Default customer on order opening
A new dine-in order SHALL use the configured default POS customer unless an authorized user explicitly selects another valid customer.

#### Scenario: Open a table
- **WHEN** an authorized waiter opens a free table
- **THEN** the server creates one Table Order with the configured default customer and returns it without requiring a customer-selection dialog

### Requirement: Idempotent and conflict-aware mutations
Every mobile order mutation SHALL carry a unique client request identifier and an expected order version so retries cannot duplicate changes and concurrent edits cannot silently overwrite one another.

#### Scenario: Retry after a response timeout
- **WHEN** a device retries a successful add-item request with the same client request identifier
- **THEN** the server returns the original result and does not add a second item

#### Scenario: Concurrent edit
- **WHEN** a device submits a new mutation based on an obsolete order version
- **THEN** the server returns a conflict with the current authoritative order and does not overwrite it silently

### Requirement: Confirmed kitchen submission
The mobile client SHALL distinguish locally prepared changes from commands confirmed by the server and SHALL display a command as sent only after the backend commits its production routing.

#### Scenario: Connection drops during send
- **WHEN** connectivity is lost while a waiter submits a command
- **THEN** the client reconciles by request identifier before retrying and the kitchen receives each line at most once

### Requirement: Offline operation is bounded
The MVP SHALL allow limited local preparation of changes for previously loaded orders but SHALL require confirmed connectivity for kitchen submission, payment and invoicing.

#### Scenario: Attempt offline payment
- **WHEN** a waiter attempts to pay without confirmed server connectivity
- **THEN** the application blocks the action, preserves the order and explains that payment requires connection

### Requirement: Realtime is reconciled
Realtime notifications SHALL trigger scoped reconciliation and SHALL NOT be treated as the sole source of order state.

#### Scenario: Resume after background suspension
- **WHEN** the application returns to the foreground after its realtime connection was suspended
- **THEN** it requests changes since its last confirmed marker and refreshes affected tables and orders

### Requirement: Mobile payment follows waiter configuration
Payment SHALL be available only when the authenticated waiter has the configured payment capability, and this rule SHALL be enforced by the server independently of button visibility.

#### Scenario: Waiter without payment permission
- **WHEN** a waiter without payment capability invokes the payment endpoint directly
- **THEN** the server rejects the request without creating a POS Invoice or payment record

### Requirement: Device credentials remain protected
The mobile application SHALL authenticate over HTTPS, store revocable tokens in protected device storage and SHALL NOT embed passwords, API secrets, database credentials or electronic-invoicing credentials.

#### Scenario: Lost device
- **WHEN** an administrator revokes a lost device session
- **THEN** subsequent API and realtime access from its token is rejected without disabling unrelated authorized devices

