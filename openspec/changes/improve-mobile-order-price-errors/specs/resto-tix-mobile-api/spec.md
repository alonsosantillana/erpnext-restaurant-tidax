## ADDED Requirements

### Requirement: Mobile item mutations report missing POS prices explicitly
The mobile facade SHALL reject an authorized catalog item whose resolved POS price is not positive before mutating the restaurant order.

#### Scenario: Catalog item has no configured price
- **WHEN** an authenticated waiter adds an authorized item whose configured POS price is absent, zero or negative
- **THEN** the server returns `ITEM_PRICE_MISSING` with HTTP 409 and performs no order mutation

#### Scenario: Catalog item has a positive configured price
- **WHEN** an authenticated waiter adds an authorized item whose configured POS price is positive
- **THEN** the entry uses that authoritative price and proceeds through the existing `TableOrder` rules

### Requirement: Kitchen submission preserves TableOrder property semantics
The mobile command operation SHALL evaluate the existing `TableOrder.send` property exactly once and SHALL NOT treat its returned data as a callable.

#### Scenario: Order has unsent items
- **WHEN** an authorized mobile command is submitted with the current order version
- **THEN** `TableOrder.send` is evaluated once before the authoritative order response is returned
