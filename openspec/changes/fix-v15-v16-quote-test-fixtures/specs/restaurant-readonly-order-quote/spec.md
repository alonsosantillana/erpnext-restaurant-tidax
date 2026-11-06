## ADDED Requirements

### Requirement: Native quote fixtures isolate context without private Frappe storage
Offline quote tests SHALL isolate and restore request-local state using the
public Local iteration/release interface available in v15 and v16.

#### Scenario: A synthetic quote completes
- **WHEN** a native quote fixture runs with an existing caller-local value
- **THEN** that original value is restored after cleanup and synthetic state is removed
- **AND** real POSInvoice pricing/tax arithmetic and all existing expected totals remain unchanged.

#### Scenario: Fixture setup or calculation raises
- **WHEN** the fixture fails before normal completion
- **THEN** cleanup still restores the caller context
- **AND** no site, network, database mutation or POS execution occurs.

#### Scenario: Frappe moves the document implementation module
- **WHEN** v15 or v16 constructs the real unsaved native document
- **THEN** only its synthetic metadata/controller read dependencies use the actual lookup module
- **AND** paired TIX pickup/delivery assertions exercise the real engine, not substituted totals.
