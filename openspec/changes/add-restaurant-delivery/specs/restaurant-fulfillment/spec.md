## ADDED Requirements

### Requirement: Explicit service type
Every restaurant order SHALL have an explicit service type of Dine In, Delivery or Pickup and SHALL NOT infer fulfillment from a table name, prefix or description.

#### Scenario: Existing dine-in order
- **WHEN** an existing order has no explicit service type during migration
- **THEN** the system assigns Dine In without changing its table, items, totals or status

#### Scenario: Create delivery without table
- **WHEN** an authorized operator creates a valid Delivery order
- **THEN** the order is persisted without a Restaurant Table and receives exactly one Delivery fulfillment

#### Scenario: Dine-in requires table
- **WHEN** a caller creates a Dine In order without an authorized table
- **THEN** the server rejects it without creating an order or fulfillment

### Requirement: Fulfillment contact and address
Delivery SHALL require a permitted Customer, contact phone and Address linked to that Customer; Pickup SHALL require a permitted Customer and contact phone without requiring an Address.

#### Scenario: Valid delivery address
- **WHEN** an operator selects an Address linked to the order Customer
- **THEN** the system stores the links and immutable customer, phone and rendered-address snapshots used for that order

#### Scenario: Address belongs to another customer
- **WHEN** a caller supplies an Address that is not linked to the selected Customer
- **THEN** the server rejects the request without exposing the other customer's address

### Requirement: Independent fulfillment lifecycle
The system SHALL manage preparation, logistics and payment as independent state dimensions and SHALL enforce fulfillment transitions on the server with actor and timestamp audit.

#### Scenario: Delivery preparation becomes ready
- **WHEN** every positive production dish in a Delivery order reaches the configured completed preparation state
- **THEN** its fulfillment transitions from Preparing to Ready exactly once

#### Scenario: New preparation round
- **WHEN** a Ready fulfillment receives and sends a new dish round
- **THEN** it returns to Preparing and becomes Ready again only after the new round completes

#### Scenario: Dispatch and delivery
- **WHEN** authorized users assign, dispatch and deliver a Ready Delivery order using the expected current state
- **THEN** it progresses through Assigned, Out for Delivery and Delivered with actor and timestamp recorded for each accepted transition

#### Scenario: Conflicting transition
- **WHEN** two clients attempt a transition based on the same earlier fulfillment state
- **THEN** at most one transition succeeds and the other receives the persisted current state

#### Scenario: Pickup completion
- **WHEN** an authorized user hands a Ready Pickup order to the customer
- **THEN** it transitions to Picked Up without using delivery-assignment states

### Requirement: Delivery fee is an invoice item
Any delivery charge SHALL be represented by at most one positive order line using the configured sale Item and SHALL flow through standard ERPNext price, tax, total and invoice calculations.

#### Scenario: Add delivery fee
- **WHEN** an operator assigns a positive manual delivery charge
- **THEN** the server adds or updates one identified fee line and the order total is recalculated authoritatively

#### Scenario: Fee excluded from kitchen
- **WHEN** a Delivery order containing the configured fee Item is sent to production
- **THEN** the fee remains billable but no kitchen or bar command is created for it

#### Scenario: Missing fee configuration
- **WHEN** an operator enters a positive fee without a valid configured sale Item
- **THEN** the server rejects the fee with a configuration message and does not create an unaccounted custom total

### Requirement: Manual delivery intake board
Restaurant Manage SHALL provide separate Delivery and Pickup intake/board views scoped to the active Company and POS Profile, updated after committed changes without requiring a browser refresh.

#### Scenario: New delivery appears in two clients
- **WHEN** one operator creates a Delivery order successfully
- **THEN** all authorized open boards reconcile and display it in the New column without F5

#### Scenario: Delivery stages are visually identifiable
- **WHEN** the operator opens the Delivery board
- **THEN** New, Preparing, Ready, Assigned, Out for Delivery and Delivery Failed use distinct semantic colors
- **AND** every stage retains a visible text label so meaning does not depend on color alone

#### Scenario: Pickup stages are visually identifiable
- **WHEN** the operator opens the Pickup board
- **THEN** New, Preparing, Ready and Picked Up use distinct semantic colors
- **AND** Picked Up remains represented by a dedicated column with a visible text label

#### Scenario: Minimized board payload
- **WHEN** the board loads or receives a realtime refresh
- **THEN** it receives only the operational summary needed for cards and retrieves full contact/address details only when an authorized user opens the order

### Requirement: External order dish mutations are serialized
Delivery and Pickup SHALL preserve the same authoritative dish behavior as Dine In when products, quantities, notes or discounts are changed in rapid succession.

#### Scenario: Add a dish while another detail is saving
- **WHEN** an operator selects a new dish while a note or line discount is being persisted
- **THEN** the new dish remains visible, both changes are serialized, and the server retains the final line without requiring F5

#### Scenario: Send immediately after the final dish
- **WHEN** an operator presses Order while the final dish or its notes are still being saved
- **THEN** the client waits for every pending mutation, reloads authoritative items and sends every retained dish to production exactly once

#### Scenario: Remove an unsent dish
- **WHEN** an operator deletes an unsent dish successfully
- **THEN** the line disappears immediately and subsequent authoritative reconciliation does not restore the deleted visual row

### Requirement: Production identifies fulfillment context
Production Center SHALL display an explicit service-type label and order identity while preserving room/table labels for Dine In.

#### Scenario: Delivery command
- **WHEN** Delivery dishes are sent to a configured Production Center
- **THEN** its command displays DELIVERY, the order identifier and customer name instead of a synthetic table

#### Scenario: Dine-in command regression
- **WHEN** a Dine In dish is sent
- **THEN** its command continues to display the real room and table

#### Scenario: Filter active commands by order source
- **GIVEN** Production Center contains active Dine In, Delivery and Pickup commands
- **WHEN** the operator selects Todos, Mesas, Entrega a domicilio or Recojo en local in the Commands view
- **THEN** only active commands from the selected source are displayed without a server reload
- **AND** the selected filter remains applied after realtime dashboard updates

#### Scenario: Notify a new active command
- **GIVEN** the Commands view completed its initial dashboard load
- **WHEN** a previously unseen active command arrives through realtime reconciliation
- **THEN** the client plays one alert sound and displays one visual notification
- **AND** polling or duplicate realtime events for the same command do not repeat the notification

### Requirement: Payment timing does not equal payment receipt
The system SHALL distinguish prepaid and cash-on-delivery intent from actual payment status and SHALL NOT treat an expected delivery payment method as money received.

#### Scenario: Prepaid order
- **WHEN** an authorized POS payment is completed for a delivery order
- **THEN** actual payment and invoice linkage use the existing transactional POS flow

#### Scenario: Cash on delivery remains unpaid
- **WHEN** an order is marked Cash on Delivery and dispatched
- **THEN** its payment remains Unpaid until an authorized collection/payment action succeeds

### Requirement: Invoice delivery mapping
When a fulfillment order is invoiced, the system SHALL validate and map its customer address and contact to applicable standard POS Invoice fields without changing the approved voucher type or emission mode selection.

#### Scenario: Invoice a delivery
- **WHEN** an authorized user pays and invoices a valid Delivery order
- **THEN** the POS Invoice contains the verified customer, address and contact, includes the delivery-fee Item, and matches the order's tax-inclusive total

### Requirement: Fulfillment authorization and privacy
All fulfillment reads and mutations SHALL enforce document, Company and POS Profile access, and realtime/list responses SHALL minimize personal information.

#### Scenario: Unauthorized cross-company access
- **WHEN** a user requests or mutates a fulfillment outside their authorized Company or POS Profile
- **THEN** the server rejects access without returning customer, phone, address or instructions

#### Scenario: Cancellation after preparation
- **WHEN** a user without elevated cancellation permission attempts to cancel an order that entered preparation
- **THEN** the server rejects the cancellation and preserves the order and fulfillment state
