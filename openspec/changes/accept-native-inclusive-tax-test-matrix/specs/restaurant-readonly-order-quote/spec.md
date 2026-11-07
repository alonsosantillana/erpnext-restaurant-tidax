## ADDED Requirements

### Requirement: Inclusive-tax test expectations are fixed by accepted native major
The offline quote tests SHALL assert exact tax 38.13 for ERPNext v15 and 38.14
for v16 at total 250 with inclusive prices, using independent literals only.

#### Scenario: The native engine calculates inclusive multi-item taxes
- **WHEN** the synthetic cart runs on an inspected supported expectation major
- **THEN** tax matches that major's fixed oracle and total remains exactly 250
- **AND** production arithmetic, numeric precision and all other assertions remain unchanged.

#### Scenario: Oracle selection is tested independently
- **WHEN** the version string is mocked to v15 or v16 without running the engine
- **THEN** the helper returns the respective fixed literal
- **AND** an unknown major fails explicitly without a default value or skip.
