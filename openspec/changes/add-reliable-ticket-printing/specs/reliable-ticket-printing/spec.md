## ADDED Requirements

### Requirement: Durable and isolated print requests

The system SHALL persist every restaurant print request with Company, source
document, route, station, idempotency key and lifecycle status before delivery.

#### Scenario: Bridge unavailable

- **WHEN** a valid invoice is completed while its print station is offline
- **THEN** the invoice remains completed
- **AND** one Pending print job remains available for later delivery

#### Scenario: Duplicate business event

- **WHEN** the same document event requests the same route more than once
- **THEN** only one active print job is created for its idempotency key

### Requirement: Acknowledged HWB delivery

The station SHALL correlate every HWB response by job id and SHALL normalize
both supported response contracts.

#### Scenario: Confirmed acceptance

- **WHEN** HWB returns success for the requested job id
- **THEN** the job becomes Accepted by HWB
- **AND** the response time and printer name, when available, are stored

#### Scenario: Ambiguous delivery

- **WHEN** the WebSocket accepted the outbound frame but no correlated response
  arrives before timeout
- **THEN** the job becomes Ambiguous
- **AND** it is not retried automatically

### Requirement: Auditable incident resolution

A station operator SHALL be able to close failed or ambiguous jobs without deleting their history.

#### Scenario: Physically confirmed ambiguous job

- **WHEN** the assigned station operator confirms an Ambiguous job was printed
- **THEN** the job becomes Confirmed Printed
- **AND** the resolving user, date and note are stored
- **AND** the job no longer contributes to Attention required

#### Scenario: Obsolete incident

- **WHEN** an assigned operator discards a Failed or Ambiguous job with a reason
- **THEN** the job becomes Cancelled without creating another print request
- **AND** its resolution remains auditable

### Requirement: Company and station routing

Every route SHALL belong to one Company and SHALL target an enabled station of
the same Company.

#### Scenario: Cross-company route

- **WHEN** a route references a station from another Company
- **THEN** validation rejects the configuration

#### Scenario: Immediate station disconnect

- **WHEN** the assigned operator disconnects an active station with its current browser lease
- **THEN** that station becomes inactive immediately
- **AND** no station or lease belonging to another Company is modified

### Requirement: Optional operational printing

Comanda and kitchen printing SHALL be independently optional and SHALL only
contain the newly sent round.

#### Scenario: Kitchen route disabled

- **WHEN** an order is sent and its kitchen route is disabled
- **THEN** order persistence and Production Center notification continue
- **AND** no kitchen print job is created

### Requirement: Print station visibility

The station page SHALL show connection, lease, pending, accepted, failed and
ambiguous state without exposing PDF payloads or documents from another Company.

#### Scenario: Company-scoped station dashboard

- **WHEN** the assigned station user opens the permanent station page
- **THEN** only jobs routed to that user active Company station are shown
- **AND** no PDF Base64 content is persisted or displayed in the job history
