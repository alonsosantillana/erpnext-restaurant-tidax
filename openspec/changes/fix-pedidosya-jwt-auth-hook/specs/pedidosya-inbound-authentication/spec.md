## ADDED Requirements

### Requirement: Middleware JWT reaches only its intended webhook

The system SHALL authenticate valid middleware JWT requests through Frappe's
standard auth hook only for the exact PedidosYa dispatch and status routes and
their declared HTTP methods, before Frappe's generic Guest rejection.

#### Scenario: Guest dispatch with valid JWT
- **WHEN** an enabled vendor receives a valid signed POST without session cookies
- **THEN** the configured enabled integration user is established for that request
- **THEN** the dispatch endpoint can acknowledge receipt with 202 or duplicate 200

#### Scenario: Attempted command redirection
- **WHEN** a request to a webhook provides a different cmd or effective override
- **THEN** authentication is rejected before establishing integration identity

#### Scenario: Unrelated route or HTTP method
- **WHEN** a JWT is supplied to another API, a suffixed route or unsupported method
- **THEN** the hook does not grant integration identity or bypass native authentication

### Requirement: Fail closed before granting integration identity

The system SHALL require a textual remote_id, enabled configuration and eligible
enabled integration user. JWT validation SHALL require a permitted HMAC algorithm,
valid signature, exp and service=middleware, and configured issuer/audience.

#### Scenario: Invalid credentials or configuration
- **WHEN** the signature, expiry, service, issuer, audience, algorithm, vendor or user is invalid
- **THEN** the request is rejected without changing identity or creating a PedidosYa order

#### Scenario: Strict expiration tolerance
- **WHEN** JWT clock leeway is configured to zero
- **THEN** zero is honored rather than replaced by the default tolerance

#### Scenario: Independent vendors
- **WHEN** a token signed for one configured vendor is sent to another with a different secret
- **THEN** authentication fails using the requested vendor's configuration

### Requirement: Preserve operational and data safety

The correction SHALL preserve endpoint JWT validation, receipt idempotency and
test-order isolation without modifying core, granting roles or updating prices.

#### Scenario: Receipt-only test
- **WHEN** test=true is processed after successful authentication
- **THEN** it may reach Test without creating commercial or kitchen documents
