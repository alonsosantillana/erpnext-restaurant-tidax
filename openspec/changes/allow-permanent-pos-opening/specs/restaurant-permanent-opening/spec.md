## ADDED Requirements

### Requirement: Explicit primary-profile opt-in
The system SHALL permit an older restaurant POS opening only when the invoice company's settings explicitly enable permanent openings and its configured primary POS profile matches the invoice.

#### Scenario: Default or unrelated profile
- **WHEN** the flag is disabled, missing or the profile does not match
- **THEN** native ERPNext opening validation applies unchanged

#### Scenario: Valid older opening
- **WHEN** opt-in is enabled and exactly one submitted Open opening exists for the primary profile with consistent company and a valid past start
- **THEN** the invoice passes opening validation without changing that opening or historical invoices

### Requirement: Opening integrity remains enforced
The system SHALL reject missing, duplicate, unsubmitted, wrong-company, future or mismatched referenced openings.

#### Scenario: Duplicate active openings
- **WHEN** multiple Open entries exist for the invoice profile regardless of company or submitted status
- **THEN** native multiple-opening rejection is preserved

#### Scenario: Invalid single opening
- **WHEN** the only Open entry is unsubmitted, company-inconsistent, future-dated or differs from the invoice opening reference
- **THEN** validation rejects it

### Requirement: Preserve financial processing
The system SHALL leave all other invoice validations, financial values, dates, stock controls, historical documents and closing behavior unchanged.

#### Scenario: Activation
- **WHEN** the administrator enables permanent opening compatibility
- **THEN** no opening is closed, recreated or redated and no historical invoice is consolidated
