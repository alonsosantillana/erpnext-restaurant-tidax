## ADDED Requirements

### Requirement: Tips are settled once through a consolidated accounting entry

The system SHALL settle multiple eligible Restaurant Tips for one waiter with exactly
one submitted Journal Entry. It SHALL create one liability debit line per tip,
referencing that tip's submitted collection Journal Entry, and one consolidated credit
to the selected payment account for the selected total.

#### Scenario: Settle collected tips for one waiter

- **GIVEN** selected tips are Collected and belong to the same company, waiter,
  liability account, and submitted POS closing
- **WHEN** an authorized user confirms a payment method and posting date
- **THEN** one balanced Journal Entry is submitted for their total
- **AND** every debit line references the corresponding collection Journal Entry
- **AND** the payment account is credited once for the consolidated total
- **AND** every selected tip becomes Settled and links to that entry

#### Scenario: Collection entry is unavailable

- **WHEN** a selected tip has no collection Journal Entry or that entry is not submitted
- **THEN** settlement is rejected without posting or changing any selected tip

#### Scenario: Mixed or previously settled selection

- **WHEN** selection contains different waiters, companies, liabilities, closings, or
  a tip not in Collected state
- **THEN** settlement is rejected without posting or changing any selected tip

#### Scenario: Concurrent settlement

- **WHEN** two requests include the same collected tip
- **THEN** row locking and state revalidation allow at most one payout

### Requirement: Settlement is authorized and tied to a closed cash session

Only restaurant cashiers and administrators SHALL settle tips. Cashiers SHALL be
limited to submitted closings belonging to their own POS opening; administrators MAY
settle any submitted closing in an accessible company.

#### Scenario: Waiter attempts payout

- **WHEN** a waiter invokes the settlement API
- **THEN** the server rejects the request

#### Scenario: Cashier settles another cashier's closing

- **WHEN** a cashier selects tips from a closing owned by another cashier
- **THEN** the server rejects the request

#### Scenario: Open session has not closed

- **WHEN** a selected tip has no submitted POS closing
- **THEN** settlement is rejected until the session is closed

### Requirement: Settlement reversal restores the payable state

Cancelling a settlement Journal Entry SHALL restore every linked tip from Settled to
Collected and clear its settlement audit fields without cancelling collection entries.

#### Scenario: Cancel consolidated settlement

- **GIVEN** a submitted settlement entry linked to several tips
- **WHEN** the entry is cancelled
- **THEN** all linked tips return to Collected
- **AND** their original collection Journal Entries remain submitted

### Requirement: Propinas Resumen supports controlled payout

The report SHALL allow management users to select eligible rows, preview the total,
and trigger settlement. It SHALL show payout audit data and SHALL omit Journal Entry
identifiers when the caller lacks Journal Entry read permission.

#### Scenario: Pay selected tips from the report

- **WHEN** a management user selects compatible collected tips and confirms payout
- **THEN** the report refreshes with Settled status and payout audit information

#### Scenario: Unauthorized report user

- **WHEN** a waiter views the report
- **THEN** payout controls are not shown
- **AND** direct API invocation remains forbidden
