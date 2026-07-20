## ADDED Requirements

### Requirement: Valid order item state transitions
The system SHALL enforce a single server-side transition model for Order Entry Item states and SHALL prevent transitions out of terminal states except through an explicitly authorized recovery action.

#### Scenario: Normal kitchen progression
- **WHEN** an authorized user advances an item through Attending, Sent, Processing, Completed, Delivering and Delivered
- **THEN** each accepted transition records the resulting state and relevant timing exactly once

#### Scenario: Invalid regression
- **WHEN** a caller attempts to move a Delivered or Invoiced item back to an earlier state without an authorized recovery action
- **THEN** the server rejects the transition and retains the terminal state

### Requirement: Atomic order mutations
Creating, editing, dividing, transferring, sending, deleting or invoicing an order MUST be atomic within the request transaction.

#### Scenario: Successful split
- **WHEN** an authorized user divides valid quantities into a second order
- **THEN** both orders and all child quantities are persisted consistently without duplicate identifiers

#### Scenario: Failure during split
- **WHEN** validation or persistence fails after the split begins
- **THEN** neither order is partially changed and no explicit internal commit prevents rollback

### Requirement: Safe deletion
The system SHALL block deletion of an order containing items that passed the configured cancellable state and SHALL NOT clear child rows before evaluating the rule.

#### Scenario: Delete untouched order
- **WHEN** an authorized user deletes an order containing only cancellable items
- **THEN** the order and children are removed through Frappe document lifecycle hooks

#### Scenario: Delete sent order
- **WHEN** a user attempts to delete an order containing a Sent, Processing, Completed, Delivered or Invoiced item
- **THEN** deletion is rejected and all order items remain unchanged

### Requirement: Document lifecycle integrity
Table Order MUST use a documented Frappe document lifecycle and MUST NOT update `docstatus` directly.

#### Scenario: Invoice completes an order
- **WHEN** a POS Invoice is submitted and linked successfully
- **THEN** Table Order reaches its final state using the selected lifecycle and runs all applicable validation and event hooks

#### Scenario: Invoice submission fails
- **WHEN** POS Invoice validation or submission fails
- **THEN** Table Order remains open and no invoice link or final `docstatus` is persisted

### Requirement: Concurrency control
The server SHALL detect conflicting mutations to the same table or order and SHALL preserve one authoritative state.

#### Scenario: Two users edit the same order
- **WHEN** two clients submit incompatible changes based on the same earlier version
- **THEN** at most one mutation succeeds and the other client is instructed to reload current state

#### Scenario: Realtime update
- **WHEN** a transaction commits successfully
- **THEN** relevant clients receive a realtime notification and reload or reconcile against persisted server state

### Requirement: Non-destructive scheduled maintenance
Scheduled jobs SHALL operate only on explicitly eligible non-terminal records and MUST preserve Delivered, Invoiced, cancelled and otherwise final states.

#### Scenario: Daily maintenance runs
- **WHEN** the scheduler evaluates orders from a previous day
- **THEN** it updates only records meeting the documented expiry rule and records the action without rewriting unrelated states
