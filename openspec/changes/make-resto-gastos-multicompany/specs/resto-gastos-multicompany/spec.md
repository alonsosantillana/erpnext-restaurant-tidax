## ADDED Requirements

### Requirement: Company-scoped expense and POS payment context
Resto Gastos SHALL require an accessible company, a submitted open POS opening,
its derived POS profile, and a payment method available in both opening and profile.
The payment account SHALL be derived from the method for that company and SHALL
be enabled, non-group and Asset-rooted.

#### Scenario: Valid company and opening
- **WHEN** a user selects an open submitted POS opening of the expense company
- **THEN** the profile and payment account SHALL be resolved from that context

#### Scenario: Inconsistent or inaccessible context
- **WHEN** the company is inaccessible, the opening is closed or belongs to another
  company, or the payment method/account does not match the opening and company
- **THEN** the server SHALL reject the expense

### Requirement: Company-specific expense numbering
The expense controller SHALL resolve its naming series from Restaurant Company
Settings for the document company rather than a shared hardcoded company series.

#### Scenario: Expenses in different companies
- **WHEN** expenses are created for companies with distinct configured series
- **THEN** each expense SHALL use the series for its own company

### Requirement: Authoritative expense detail validation
Each detail SHALL reference an enabled item from the GASTOS item group and a
positive amount. The server SHALL recalculate the total from the detail amounts.

#### Scenario: Forged total
- **WHEN** a caller supplies valid detail rows and a manipulated document total
- **THEN** the saved total SHALL equal the server-calculated sum of the rows

#### Scenario: Invalid expense detail
- **WHEN** a detail references a disabled/non-expense item or a nonpositive amount
- **THEN** the server SHALL reject the expense

### Requirement: Company-isolated expense reporting
Resumen Cierre de Caja SHALL scope submitted expenses by the closing company.
Historical expenses without a company SHALL NOT be automatically reassigned.

#### Scenario: Cross-company expense
- **WHEN** the report calculates a closing for one company
- **THEN** expenses belonging to another company or without a matching company
  SHALL NOT reduce that closing's amount

## Historical scope and subsequent changes

This operational-only change predates account-resto-gastos-on-submit. Its original
exclusion of journal entries describes historical scope, not the current combined
behavior. Company isolation and the separately implemented accounting requirements
are read together; this documentation update introduces neither behavior.
