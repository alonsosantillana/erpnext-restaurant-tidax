## ADDED Requirements

### Requirement: Company-specific reservation identity

The system SHALL name every reservation using the configured Company abbreviation,
year and an independent sequential counter.

#### Scenario: Reservation name

- **WHEN** a reservation is inserted for a Company whose abbreviation is `ECS`
- **THEN** its name follows `RES-ECS-YYYY-#####`
- **AND** another Company's counter is independent

### Requirement: Server-authoritative availability

The system SHALL reject overlapping active reservations for any assigned table after
applying the configured preparation and cleanup buffers.

#### Scenario: Conflicting table

- **WHEN** an active reservation overlaps another active reservation for the same table
- **THEN** the server rejects the change with the conflicting reservation and period

#### Scenario: Non-blocking terminal state

- **WHEN** an overlapping reservation is Cancelled, Completed or No Show
- **THEN** it does not block the table

### Requirement: Capacity-aware table assignment

The system SHALL validate assigned tables, their Company and their total seating
capacity before confirming a reservation.

#### Scenario: Insufficient capacity

- **WHEN** the guest count exceeds the combined capacity and override is disabled
- **THEN** confirmation is rejected

### Requirement: Idempotent seating

The system SHALL create at most one Table Order from a reservation.

#### Scenario: Seat confirmed reservation

- **WHEN** an authorized user seats an Arrived or Confirmed reservation
- **THEN** one Table Order is created from the primary table and configured customer
- **AND** the reservation stores its link and becomes Seated

#### Scenario: Repeated seating request

- **WHEN** seating is requested again after a Table Order was linked
- **THEN** the existing Table Order is returned without creating another

### Requirement: Reservation lifecycle audit

The system SHALL record who and when confirmed, arrived, seated, cancelled or marked
the reservation as No Show.

#### Scenario: Invoice completion

- **WHEN** the linked Table Order becomes Invoiced
- **THEN** the reservation becomes Completed

### Requirement: Operational visibility

The system SHALL provide a calendar/agenda and make upcoming table reservations
visible from Restaurant Manage with realtime refresh signals.

#### Scenario: Reservation update

- **WHEN** an active reservation is created or changes state or tables
- **THEN** subscribed restaurant views receive a refresh event

### Requirement: In-form customer creation

The system SHALL allow an authorized reservation operator to create a Customer without leaving the reservation form.

#### Scenario: Create and assign customer

- **WHEN** a user with Customer creation permission uses `Nuevo cliente`, enters a valid DNI/RUC and confirms the API preview
- **THEN** the verified Customer is created or reused and assigned to the reservation
- **AND** the reservation name, phone and email are populated from the Customer
- **AND** users without creation permission do not see the action
