## ADDED Requirements

### Requirement: Durable pre-account state

The system SHALL persist the latest successful pre-account request on the active
Table Order with requesting user, timestamp and a deterministic monetary
signature.

#### Scenario: Account print is durably queued

- **WHEN** an authorized user presses Cuenta and an ACCOUNT job is enqueued
- **THEN** the active order becomes `Requested`
- **AND** requesting user, request time and current monetary signature are stored

#### Scenario: Account print cannot be queued

- **WHEN** ACCOUNT routing, permission or station validation fails
- **THEN** no new pre-account state is stored
- **AND** the table retains its previous authoritative state

### Requirement: Monetary changes invalidate the pre-account

The system SHALL identify when the current chargeable content no longer matches
the latest requested pre-account.

#### Scenario: Chargeable content changes

- **WHEN** a requested order changes product, quantity, rate or discount
- **THEN** its pre-account becomes `Outdated`
- **AND** the original request audit remains available

#### Scenario: Non-monetary operation changes

- **WHEN** only a dish note or production status changes
- **THEN** a requested pre-account remains `Requested`

#### Scenario: Outdated account is reprinted

- **WHEN** Cuenta is successfully requested again
- **THEN** status returns to `Requested`
- **AND** the signature, user and timestamp represent the new request

### Requirement: Authoritative table visualization

The floor map SHALL derive and display pre-account state from active orders and
SHALL reconcile it in real time across sessions.

#### Scenario: All active orders have current pre-accounts

- **WHEN** every active order on a table is `Requested`
- **THEN** the table uses a distinct amber state
- **AND** a textual CUENTA indicator is visible

#### Scenario: An active pre-account is outdated

- **WHEN** any active order on the table is `Outdated`
- **THEN** the table shows an explicit reprint warning distinct from the current state

#### Scenario: Only some active orders requested an account

- **WHEN** a table has multiple active orders and at least one has no current pre-account
- **THEN** the table is not represented as ready to be released

#### Scenario: Order is transferred

- **WHEN** a requested order moves to another table
- **THEN** the source table is recalculated
- **AND** the destination table derives the transferred order state

#### Scenario: Order is invoiced

- **WHEN** the order status becomes `Invoiced`
- **THEN** it no longer contributes pre-account state to the table

### Requirement: Company-isolated notifications

Pre-account table aggregation and realtime payloads SHALL use only active orders
belonging to the table Company and SHALL expose no customer or tax data.

#### Scenario: Order from another company

- **WHEN** pre-account aggregation is calculated for a table
- **THEN** orders belonging to another Company are ignored
