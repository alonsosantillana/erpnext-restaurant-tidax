## Purpose

Define authorization, accounting, audit, concurrency, and reporting behavior for
cancelling or rectifying non-fiscal restaurant tips after payment.

## ADDED Requirements

### Requirement: Tip management is role and shift controlled

The system SHALL authorize cancellation and rectification on the server. A user with
the cashier role SHALL manage only tips linked to an open POS Opening Entry. A user
with the restaurant administrator role SHALL also manage eligible tips after closing.
A waiter without either role SHALL NOT manage tips.

#### Scenario: Cashier changes a tip in an open shift

- **GIVEN** the caller has the cashier role and access to the tip Company
- **AND** the related POS Opening Entry is submitted and has no submitted closing
- **WHEN** the caller cancels or rectifies an eligible tip
- **THEN** the system permits the operation

#### Scenario: Cashier attempts to change a closed-shift tip

- **GIVEN** the related opening has a submitted POS Closing Entry
- **WHEN** a caller with only the cashier role requests cancellation or rectification
- **THEN** the system rejects the operation

#### Scenario: Restaurant administrator changes a historical tip

- **GIVEN** the caller has the restaurant administrator role and Company access
- **WHEN** the caller manages an eligible tip after closing
- **THEN** the system permits the operation

#### Scenario: Waiter attempts to manage a tip

- **GIVEN** the caller has only the waiter role
- **WHEN** the caller invokes a tip-management API
- **THEN** the system rejects the operation

#### Scenario: User lacks Company access

- **WHEN** a caller requests a change to a tip from a Company the caller cannot use
- **THEN** the system rejects the operation without disclosing or changing the tip

### Requirement: Tip cancellation preserves accounting and audit integrity

The system SHALL require a meaningful cancellation reason, cancel the submitted tip
Journal Entry, mark the Restaurant Tip as Cancelled, and record the actor and time.
It SHALL NOT modify the linked POS Invoice or its electronic fiscal document.

#### Scenario: Cancel an eligible collected tip

- **GIVEN** a collected, unsettled tip with a submitted collection Journal Entry
- **WHEN** an authorized user confirms cancellation with a reason of at least five characters
- **THEN** the system cancels the Journal Entry
- **AND** marks the tip as Cancelled
- **AND** stores the reason, user, and timestamp
- **AND** leaves the POS Invoice unchanged

#### Scenario: Cancellation reason is insufficient

- **WHEN** an authorized user submits a blank or shorter cancellation reason
- **THEN** the system rejects the request without changing accounting or tip state

#### Scenario: Settled tip is cancelled

- **GIVEN** the tip has already been settled or paid out
- **WHEN** an authorized user requests cancellation
- **THEN** the system rejects the request and requires settlement reversal first

### Requirement: Rectification creates an auditable replacement

The system SHALL implement rectification as cancellation of the original tip followed
by creation and posting of one linked replacement tip. The corrected amount MUST be
positive and different from the original amount.

#### Scenario: Rectify a collected tip

- **GIVEN** an eligible collected tip
- **WHEN** an authorized user confirms a different positive amount and a valid reason
- **THEN** the original Journal Entry is cancelled
- **AND** the original tip is marked Cancelled
- **AND** a new collected tip and Journal Entry are created for the corrected amount
- **AND** the original and replacement records link to each other

#### Scenario: Invalid corrected amount

- **WHEN** the corrected amount is zero, negative, or equal to the original amount
- **THEN** the system rejects rectification without changing the original tip

#### Scenario: Replacement posting fails

- **WHEN** original cancellation succeeds but replacement creation or posting fails
- **THEN** the system rolls back the complete rectification
- **AND** the original tip and Journal Entry remain active

### Requirement: Concurrent changes result in one active tip version

The system MUST serialize cancellation and rectification of the same active tip and
MUST maintain at most one active tip for a POS Invoice.

#### Scenario: Two users rectify the same tip concurrently

- **WHEN** two authorized requests target the same active tip
- **THEN** the system locks and revalidates the record
- **AND** only the first valid operation succeeds
- **AND** no duplicate active replacement is created

#### Scenario: POS Invoice is cancelled after rectification

- **GIVEN** a tip was rectified and the replacement is active
- **WHEN** the linked POS Invoice is cancelled
- **THEN** the system cancels every remaining active tip and its submitted Journal Entry

### Requirement: Tip reporting supports cash-opening reconciliation and audit

Propinas Resumen SHALL allow filtering by POS opening and closing, include opening and
closing context, link rows to Restaurant Tip, and optionally include cancelled tips.
Journal Entry identifiers SHALL be returned only when the caller may read them.

#### Scenario: Cashier reports one opening

- **WHEN** a cashier selects a POS Opening Entry
- **THEN** the report limits rows to that opening
- **AND** shows its cashier, opening time, and closing context when available

#### Scenario: Report includes cancelled tips

- **WHEN** the user enables Incluir anuladas
- **THEN** cancelled original tips appear with reason, actor, time, and correction links
- **AND** active totals remain distinguishable from cancelled records

#### Scenario: Caller cannot read Journal Entry

- **GIVEN** the caller can run Propinas Resumen but cannot read Journal Entry
- **WHEN** the report is generated
- **THEN** the Journal Entry column and values are omitted

### Requirement: Tips remain editable before payment

Before a POS Invoice is submitted, the payment dialog SHALL allow an authorized user
to change the proposed tip amount or set it to zero without creating accounting entries.

#### Scenario: Remove a tip before payment

- **WHEN** the user changes the proposed tip to zero before confirming payment
- **THEN** the invoice is processed without a Restaurant Tip or tip Journal Entry
