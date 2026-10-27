## ADDED Requirements
### Requirement: Callback event transport
The application SHALL preserve the callback business event in method kwargs through Frappe enqueue without using its reserved event parameter.
#### Scenario: Queued callback
- **WHEN** any acceptance, rejection, preparation, pickup or recovery producer enqueues a callback
- **THEN** callback_event reaches send_callback and queue policy, IDs and rejection arguments are preserved
### Requirement: Direct-call compatibility
The handler SHALL accept legacy positional and named event arguments and reject missing, unsupported or contradictory event arguments before document access.
#### Scenario: Compatible direct call
- **WHEN** a caller supplies one supported event using the legacy event argument
- **THEN** the existing HTTP contract and notification flag are preserved
#### Scenario: Invalid arguments
- **WHEN** an event is missing, unsupported or conflicts with callback_event
- **THEN** the handler raises an explicit error and performs no document or HTTP access
### Requirement: Development validation
Validation SHALL run exclusively in development with synthetic records and isolated queue and receiver resources.
#### Scenario: Callback retry
- **WHEN** the receiver fails a callback and the targeted scheduled recovery job runs again
- **THEN** failure leaves the notification unconfirmed and a later successful response confirms it
#### Scenario: Cleanup
- **WHEN** validation completes or fails
- **THEN** test URLs and test cache are cleared, temporary processes stop, and existing operational documents and configuration remain unchanged
