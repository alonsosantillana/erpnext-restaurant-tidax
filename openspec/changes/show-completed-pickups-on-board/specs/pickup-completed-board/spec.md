## ADDED Requirements

### Requirement: Pickup completion visibility by day
The Pickup board SHALL display paid picked-up orders for the selected completion
date alongside outstanding orders of any date, within the existing list limits.

#### Scenario: Paid pickup completed today
- **WHEN** a permitted pickup is marked Picked Up and Paid on the selected completion day
- **THEN** its card is displayed in Picked Up with no increase in outstanding counts

#### Scenario: Order created earlier
- **WHEN** an order was created yesterday and its Picked Up transition occurred today
- **THEN** it is eligible for today's completed cards

#### Scenario: Later edit or payment
- **WHEN** a paid picked-up order was completed yesterday but modified today
- **THEN** it is not included in today's completed cards based on modified

#### Scenario: Outstanding older pickup
- **WHEN** an order of a previous day remains pending or was picked up but remains unpaid
- **THEN** it remains visible and counted as outstanding regardless of completion-date selection

### Requirement: Backward-compatible authorized reads
Completion queries SHALL retain authenticated document access and the active
Company and POS Profile scope without changing orders, payments or transitions.

#### Scenario: Historical request or Delivery
- **WHEN** an existing client omits completed_date, requests include_closed=1, or uses Delivery
- **THEN** the existing visibility contract remains unchanged

#### Scenario: Invalid date or unauthorized access
- **WHEN** a completion date is invalid or access is not permitted
- **THEN** the server rejects the query without returning records outside authorized context

### Requirement: Independent counters and current response
The client SHALL source outstanding totals from the count API, preserve selected
dates during reconciliation, and discard responses for obsolete view requests.

#### Scenario: Terminal cards coexist with outstanding cards
- **WHEN** the server returns completed paid cards and active cards
- **THEN** the terminal column counts visible completed cards but pending badges use server outstanding counts

#### Scenario: Date changes before response
- **WHEN** an operator changes the date or view while an earlier request is pending
- **THEN** only the response for the latest visible request is rendered
