## ADDED Requirements

### Requirement: Validated POS Invoice creation
The system SHALL validate actor, company, POS Profile, customer, identity data, items, stock and payments before creating and submitting a POS Invoice.

#### Scenario: Valid paid order
- **WHEN** an authorized cashier pays a valid order with payment totals equal to the invoice total
- **THEN** one POS Invoice is submitted and atomically linked to the order

#### Scenario: Invalid payment total
- **WHEN** payment totals do not satisfy the invoice total and configured tolerance
- **THEN** invoice creation is rejected without closing the order or persisting partial payment rows

### Requirement: Configured tax document selection
Invoice series, tax document type, identity rules, print format and related SUNAT values MUST be resolved from validated configuration for the order company and operating context.

#### Scenario: Boleta with DNI
- **WHEN** a customer and transaction meet the configured boleta rules
- **THEN** the invoice uses the approved boleta series and identity codes for that company

#### Scenario: Factura with RUC
- **WHEN** a customer and transaction meet the configured factura rules
- **THEN** the invoice uses the approved factura series and RUC identity codes for that company

#### Scenario: Explicit receipt selection is independent of diners
- **WHEN** the cashier selects Boleta or Factura for an order with any valid `dinners` value
- **THEN** the selected receipt type and its configured series are used, while `dinners` remains only the number of diners

#### Scenario: Missing tax configuration
- **WHEN** the required series or tax mapping is absent
- **THEN** submission is blocked with a configuration error and no fallback hardcoded value is used

### Requirement: Correct discount and gratuity treatment
The system SHALL preserve ERPNext totals and approved TIDAX/SUNAT treatment for line discounts, global discounts, partial gratuity and total gratuity.

#### Scenario: Mixed discounted items
- **WHEN** an order contains regular, line-discounted and free items
- **THEN** taxable totals, discount totals and free amounts on the invoice match the approved calculation fixture

#### Scenario: One hundred percent global discount
- **WHEN** an approved transaction applies a total global discount
- **THEN** the invoice records gratuity and totals according to the approved rule without inventing a nonzero selling rate

### Requirement: Authentic audit ownership
The app MUST preserve Frappe's authenticated creator and modifier values and MUST NOT assign a hardcoded invoice owner.

#### Scenario: Cashier creates invoice
- **WHEN** a cashier submits an invoice
- **THEN** the audit fields identify the authenticated cashier and any business waiter assignment remains in a separate field

### Requirement: Recoverable electronic invoicing
Electronic document submission SHALL be idempotent and recoverable, and a remote failure MUST NOT duplicate or corrupt the local POS Invoice.

#### Scenario: SUNAT provider accepts document
- **WHEN** the configured provider accepts the submitted invoice
- **THEN** the app stores the approved status and permitted response references without exposing credentials

#### Scenario: Provider timeout after local submission
- **WHEN** the local invoice is submitted but the provider times out
- **THEN** the invoice remains locally consistent in a retryable electronic state and retry does not create a second POS Invoice

### Requirement: Controlled printing
Printing SHALL use `silent_print` with WebApp Hardware Bridge, validated printer and print-format configuration, and SHALL be isolated from the transaction that persists an order, comanda or invoice.

#### Scenario: Silent print unavailable
- **WHEN** the invoice exists but silent printing is not installed or fails
- **THEN** the sale remains valid and the user receives a retry or standard-print option

#### Scenario: Ticket-printer job succeeds
- **WHEN** an authorized user prints a configured comanda, boleta or factura and the hardware bridge accepts the job
- **THEN** the job uses the configured printer and format without duplicating or changing the commercial document
