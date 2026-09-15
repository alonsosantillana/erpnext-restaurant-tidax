# Resto TIX Mobile pre-account API

## MODIFIED Requirements

### Requirement: Return authorized restaurant tables

The Mobile API SHALL return active orders only for tables authorized by the active ERPNext context, including the normalized pre-account state required to mirror the restaurant floor.

#### Scenario: Authorized active order has a requested pre-account

- **GIVEN** the user can read the active order
- **AND** its `pre_account_status` is `Requested`
- **WHEN** the user requests the table list
- **THEN** the active-order summary includes `pre_account_status: Requested`

#### Scenario: Unknown or empty pre-account state

- **WHEN** an active order contains no recognized pre-account state
- **THEN** the API returns `pre_account_status: null`

### Requirement: Return company presentation settings

The authenticated context SHALL expose the active restaurant company's requested and outdated pre-account colors.

#### Scenario: Company has configured colors

- **WHEN** the user requests the authenticated context
- **THEN** the response contains both pre-account table-state colors
- **AND** does not expose unrelated restaurant settings
