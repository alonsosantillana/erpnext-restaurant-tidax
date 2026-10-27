## ADDED Requirements
### Requirement: Bounded callback token renewal
The outbound client SHALL renew authentication after the first callback HTTP 401 and retry the same callback at most once per invocation.
#### Scenario: Cached token rejected
- **WHEN** the first callback returns HTTP 401 and fresh authentication succeeds
- **THEN** the same callback is repeated once with the current bearer token and its successful result is returned
#### Scenario: Renewal or replay fails
- **WHEN** renewed login fails or the second callback fails
- **THEN** the failure propagates without a third callback request and the notification remains unconfirmed
#### Scenario: Other failure
- **WHEN** a callback fails with a non-401 HTTP status or a network exception
- **THEN** it propagates without immediate token invalidation, login or callback replay
### Requirement: Scoped race-safe token cache
Token invalidation SHALL remove only the rejected integration token using a site-scoped atomic comparison and SHALL discard stale request-local copies for that key.
#### Scenario: Concurrent renewal
- **WHEN** another worker replaces the token before atomic invalidation
- **THEN** its newer token is preserved and may be reused without an additional login
#### Scenario: Cache isolation
- **WHEN** renewal invalidates a rejected token
- **THEN** other integration and site tokens and cache entries remain unchanged
### Requirement: Preserve callback safety and contracts
Authentication recovery SHALL preserve HTTPS validation, allowed hosts, timeouts, payload semantics and success-only notification flags.
#### Scenario: Prepared callback replay
- **WHEN** a prepared callback is retried after HTTP 401
- **THEN** both requests omit JSON and use the configured timeout and HTTPS destination
### Requirement: Development-only verification
Verification SHALL use synthetic development data, a temporary certificate-validated receiver and an isolated queue without operational orders or shared scheduler consumption.
#### Scenario: Completion or failure cleanup
- **WHEN** verification ends
- **THEN** fictitious callback URLs and token cache are removed, temporary processes stop and existing operational data/configuration remain unchanged
