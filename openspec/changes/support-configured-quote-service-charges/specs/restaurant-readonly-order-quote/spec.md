## ADDED Requirements

### Requirement: Read-only quotes SHALL respect configured tax and service charges
The service SHALL calculate the supported rows of the bound company/POS template
with native ERPNext arithmetic, without fixed charge percentages or master writes.

#### Scenario: Restaurant configures only tax
- **WHEN** a supported Pickup or Delivery quote uses a tax-only template
- **THEN** no service charge is invented and native inclusive/exclusive totals apply.

#### Scenario: Restaurant configures a service charge
- **WHEN** the template includes a readable active same-company Income/Expense leaf
  charge account with supported account/report type
- **THEN** the configured rate participates once in native whole-cart calculation
- **AND** tax remains the combined native taxes-and-charges aggregate.

#### Scenario: Delivery is priced separately
- **WHEN** a Delivery quote has an eligible native fee price
- **THEN** exactly one fee line is included in the same native calculation
- **AND** Pickup has no fee line or fee amount.

### Requirement: Additional charge support SHALL preserve fail-closed boundaries
Charge support SHALL NOT enable arbitrary settlement/balance-sheet accounts or
weaken permissions, tenant checks, disabled/group checks or tax row limits.

#### Scenario: Charge account eligibility changes
- **WHEN** root type, report type, account type or configured rate changes
- **THEN** the fingerprint changes or the quote is rejected without side effects.

#### Scenario: Unsupported account or template row is selected
- **WHEN** scope/permission/account/row eligibility fails
- **THEN** the quote is rejected, no values are substituted and no document is saved.
