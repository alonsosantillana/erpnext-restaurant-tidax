## Purpose

Permitir que caja capture cobros simples o mixtos de forma compacta y escalable,
sin que la cantidad de medios configurados aumente la altura del formulario POS.

## ADDED Requirements

### Requirement: Compact payment method selection

The payment form SHALL display one active sale payment method selector and one
active amount field regardless of how many methods are configured in the current
POS Profile.

#### Scenario: Profile has many payment methods

- **WHEN** the payment form opens with two or more configured methods
- **THEN** all methods are available in one selector
- **AND** the form does not render one permanent amount field per available method

#### Scenario: Default method is available

- **WHEN** the form opens and the POS Profile identifies a default method
- **THEN** that method is selected
- **AND** its amount is initialized with the unpaid sale balance

#### Scenario: No method is marked as default

- **WHEN** the form opens without a configured default method
- **THEN** the first available authorized method is selected
- **AND** the sale balance remains available for allocation

### Requirement: Mixed payment allocation

The payment form SHALL allow the payable sale amount to be distributed among
multiple authorized methods while maintaining at most one allocation per method.

#### Scenario: Add a second payment method

- **WHEN** the cashier allocates part of the amount and selects another method
- **THEN** both positive allocations appear in a compact summary
- **AND** the paid and pending totals are recalculated immediately

#### Scenario: Select an already allocated method

- **WHEN** the cashier selects a method that already has an allocation
- **THEN** its existing amount is loaded for editing
- **AND** no duplicate allocation is created

#### Scenario: Remove an allocation

- **WHEN** the cashier removes an allocated method
- **THEN** that method contributes zero to the sale payment
- **AND** paid, pending and change values are recalculated

### Requirement: Payment amount entry

The active amount field SHALL work with the existing numeric keypad and SHALL
update the selected method allocation without changing other method allocations.

#### Scenario: Payment modal has desktop space

- **WHEN** the payment form is shown at its normal desktop width
- **THEN** the payment editor and numeric keypad are aligned in adjacent columns
- **AND** the keypad uses the available column with uniform touch targets

#### Scenario: Payment modal is narrow

- **WHEN** the available viewport cannot preserve both columns
- **THEN** the numeric keypad stacks below the payment editor without overflow

#### Scenario: Enter amount with keypad

- **WHEN** the cashier selects a method and enters a value using the numeric keypad
- **THEN** only that method allocation is updated
- **AND** the compact summary reflects the new value

#### Scenario: Allocate remaining balance

- **WHEN** the cashier changes to an unallocated method
- **THEN** the active amount defaults to the positive pending sale balance
- **AND** the cashier can edit it before payment

### Requirement: Fiscal payment compatibility

The compact form MUST submit the same positive method-to-amount structure expected
by the existing invoice flow and MUST preserve the current total reconciliation.

#### Scenario: Simple payment is submitted

- **WHEN** one method covers the payable sale amount
- **THEN** the server receives one positive entry for that method
- **AND** invoice creation follows the existing flow

#### Scenario: Mixed payment is submitted

- **WHEN** multiple allocations exactly cover the payable sale amount
- **THEN** the server receives one positive entry per allocated method
- **AND** their sum equals the fiscal payable amount

#### Scenario: Allocation does not reconcile

- **WHEN** the sale allocations do not equal the payable amount within the existing tolerance
- **THEN** payment is blocked with the existing reconciliation message
- **AND** no invoice request is sent

### Requirement: Independent tip collection

The compact sale payment controls SHALL remain independent from the tip amount and
tip collection method.

#### Scenario: Tip is entered

- **WHEN** tips are enabled and the cashier enters a tip
- **THEN** the sale allocations continue to reconcile only against the fiscal sale
- **AND** the tip retains its separate collection-method selector
