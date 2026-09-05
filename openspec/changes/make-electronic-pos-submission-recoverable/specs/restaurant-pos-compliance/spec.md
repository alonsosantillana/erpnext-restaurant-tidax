## ADDED Requirements

### Requirement: Durable restaurant electronic submission

Restaurant Manage SHALL persist and enqueue electronic POS Invoice submission only after the local sale transaction commits.

#### Scenario: Electronic payment succeeds locally

- **WHEN** an electronic restaurant payment creates and links a submitted POS Invoice
- **THEN** the invoice is marked `Queued`
- **AND** one provider synchronization job is enqueued after commit
- **AND** the browser is released without waiting for the provider

#### Scenario: Local payment rolls back

- **WHEN** POS Invoice or Table Order persistence fails
- **THEN** no provider synchronization job is enqueued

### Requirement: Idempotent provider synchronization

Every automatic or manual attempt SHALL consult Nubefact before generation and SHALL serialize attempts for the same POS Invoice.

#### Scenario: Provider accepted but response was lost

- **GIVEN** the local invoice has no stored hash
- **AND** Nubefact already knows the document
- **WHEN** synchronization retries
- **THEN** the provider state is persisted without generating a duplicate

#### Scenario: Provider does not know the document

- **WHEN** consultation returns `not_found` or code `24`
- **THEN** the existing POS Invoice is submitted once
- **AND** no second POS Invoice is created

### Requirement: Recoverable lifecycle

The system SHALL expose a sanitized persistent lifecycle and recover abandoned or transiently failed submissions.

#### Scenario: Provider timeout

- **WHEN** provider confirmation times out
- **THEN** the invoice remains `Retry Required`
- **AND** a later attempt consults before generation
- **AND** credentials and fiscal payloads are absent from the stored error

#### Scenario: Browser closes after payment

- **WHEN** the browser closes after the sale commits
- **THEN** the background job continues independently
- **AND** a periodic recovery job can requeue an abandoned attempt

#### Scenario: Historical unmarked invoice

- **GIVEN** an old electronic invoice has no restaurant emission lifecycle
- **WHEN** periodic recovery runs
- **THEN** it is not sent automatically
