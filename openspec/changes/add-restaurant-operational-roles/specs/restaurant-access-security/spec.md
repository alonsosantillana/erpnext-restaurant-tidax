# Restaurant access security

## ADDED Requirements

### Requirement: Restaurant operations use explicit least-privilege roles

The system SHALL provide `resto_admin`, `resto_cajero`, `resto_mozo`, `resto_cocina`, and `resto_delivery` roles with responsibilities separated between configuration, cashiering, table service, production, and fulfillment.

#### Scenario: Cashier opens an order without layout permission

- **GIVEN** a user with `resto_cajero`, read access to a restaurant table, and create access to `Table Order`
- **WHEN** the user opens an empty table and creates its first order
- **THEN** the order is created
- **AND** the user is not granted write access to configure the room or table layout

#### Scenario: Waiter cannot invoice by restaurant role alone

- **GIVEN** a user with `resto_mozo` but without create permission on `POS Invoice`
- **WHEN** the user attempts to create an invoice from a table order
- **THEN** the operation is denied

#### Scenario: Kitchen updates production without layout permission

- **GIVEN** a user with `resto_cocina`, read access to the Production Center, and write access to `Table Order`
- **WHEN** the user advances a dish production state
- **THEN** the dish state is updated
- **AND** the user is not granted write access to restaurant layout configuration

### Requirement: Company restrictions remain authoritative

Restaurant roles SHALL NOT bypass Company user permissions, the user's effective restaurant Company, or its configured POS Profile.

#### Scenario: User cannot access another company's restaurant data

- **GIVEN** an operational user restricted to one Company
- **WHEN** the user requests restaurant objects or orders from another Company
- **THEN** the records are excluded or access is denied

### Requirement: Legacy restaurant users retain equivalent access

The migration SHALL add the equivalent `resto_*` role to users with supported legacy restaurant roles without removing their existing assignments.

#### Scenario: Legacy cashier is migrated

- **GIVEN** a user with the legacy `Cajero` role
- **WHEN** the role migration runs
- **THEN** the user also receives `resto_cajero`
- **AND** the `Cajero` role remains assigned
