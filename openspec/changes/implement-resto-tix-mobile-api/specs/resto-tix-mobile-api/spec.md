## ADDED Requirements

### Requirement: Resto Tix uses an authorized mobile facade
The system SHALL expose versioned, use-case-specific mobile operations and SHALL NOT allow Resto Tix to invoke arbitrary DocTypes or document methods.

#### Scenario: Unsupported arbitrary method
- **WHEN** a mobile client supplies a DocType or method name outside the versioned contract
- **THEN** the server rejects the request without invoking that target

### Requirement: ERPNext remains commercially authoritative
The system SHALL calculate restaurant prices, taxes, totals, permissions, production routes and order state in ERPNext using the existing restaurant domain.

#### Scenario: Catalog and order parity
- **WHEN** the same authorized POS Profile and order are viewed from Restaurant Manage and Resto Tix
- **THEN** both clients receive the same persisted price, tax, quantity, note, status and total values

### Requirement: Mobile access is context-bound
Every mobile operation SHALL validate the authenticated user and the requested Company, POS Profile, room, table and order.

#### Scenario: Cross-room request
- **WHEN** a waiter requests a table outside the rooms granted by Restaurant Permission
- **THEN** the server rejects the operation without disclosing the active order or customer

### Requirement: Mobile mutations are idempotent
Every mobile mutation SHALL require a unique client request identifier and SHALL persist enough result information to return the original outcome after a retry.

#### Scenario: Add-item response is lost
- **WHEN** an add-item operation commits but its response is lost and the device retries the same request identifier and payload
- **THEN** the server returns the original authoritative result without adding another quantity or line

#### Scenario: Request identifier is reused with a different payload
- **WHEN** a device reuses a confirmed request identifier for a different action or payload
- **THEN** the server rejects the request and performs no new mutation

### Requirement: Concurrent order edits are explicit
Every mobile order mutation SHALL compare an expected version while holding the order mutation lock.

#### Scenario: Stale order version
- **WHEN** another client changed the order after the device obtained its expected version
- **THEN** the server returns a conflict and the current authorized order without overwriting the newer state

### Requirement: Kitchen submission is confirmed once
Resto Tix SHALL show a command as sent only after ERPNext commits its production routing, and a retry SHALL NOT route the same lines twice.

#### Scenario: Network interruption during command submission
- **WHEN** connectivity fails after the server commits a command but before the device receives its response
- **THEN** reconciliation by request identifier returns the confirmed command and no duplicate production entries are created

### Requirement: MVP financial operations are excluded
The first Resto Tix API version SHALL NOT expose payment, POS Invoice creation or electronic-invoicing mutations.

#### Scenario: Mobile client attempts payment
- **WHEN** the MVP client calls an unimplemented or internal payment operation
- **THEN** the server rejects it without creating a POS Invoice, payment or electronic document

### Requirement: Production traffic is encrypted
Production mobile authentication and API traffic SHALL use HTTPS with a valid certificate, and device credentials SHALL be revocable and stored only in protected device storage.

#### Scenario: Production origin uses plain HTTP
- **WHEN** the application is configured for production with an HTTP API origin
- **THEN** release validation fails and the production build is not approved
