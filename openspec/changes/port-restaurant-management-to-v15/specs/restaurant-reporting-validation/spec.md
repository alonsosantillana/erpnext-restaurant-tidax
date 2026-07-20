## ADDED Requirements

### Requirement: Accurate company-scoped reports
Every restaurant report SHALL apply the selected company, authorized date range, valid document statuses and relevant user permissions.

#### Scenario: Multi-company report
- **WHEN** an authorized user runs a report for Company A during a date range
- **THEN** totals include only qualifying Company A records in that range

#### Scenario: Cancelled transaction
- **WHEN** a POS Invoice or source document is cancelled
- **THEN** it is excluded unless the report explicitly documents and labels cancelled records

### Requirement: Correct calendar boundaries
Date aggregation SHALL handle all months, year transitions, time zones and empty ranges without undefined values or reversed dates.

#### Scenario: December report
- **WHEN** a user requests December of a valid year
- **THEN** the report uses December 1 through December 31 of that year

#### Scenario: Invalid filter
- **WHEN** a required year, month, company or date range is invalid
- **THEN** the report returns a user-facing validation error rather than executing with undefined bounds

### Requirement: Bounded and performant queries
Operational queries SHALL select only required fields, use parameterized filters and remain bounded for normal interactive use.

#### Scenario: Large dataset
- **WHEN** a report or kitchen endpoint runs against representative production volume
- **THEN** it completes within the agreed performance threshold without unrestricted `SELECT *` or unbounded result sets

### Requirement: Automated critical-path tests
The repository SHALL contain meaningful tests for runtime compatibility, security, order lifecycle, POS invoicing and reports.

#### Scenario: Test suite execution
- **WHEN** the app test suite runs on the supported v15 matrix
- **THEN** tests create their own fixtures, assert business outcomes and leave the database isolated

#### Scenario: Permission regression
- **WHEN** a protected endpoint is tested as Guest or an unauthorized role
- **THEN** the test confirms rejection and no data mutation

### Requirement: End-to-end v15 qualification
Release readiness MUST require documented clean-install, upgrade and browser-based end-to-end results on an isolated v15 site.

#### Scenario: Clean-site qualification
- **WHEN** the release candidate is installed on a clean supported site
- **THEN** install, migrate, build, login, page load and the full restaurant transaction flow pass the checklist

#### Scenario: Upgrade qualification
- **WHEN** the release candidate upgrades a representative copy of a 1.7.7 site
- **THEN** metadata and business data remain consistent and documented reconciliation checks pass

### Requirement: Evidence-based release record
The change record MUST document commands, versions, test results, deviations, unresolved risks and rollback readiness before implementation is declared complete.

#### Scenario: Release review
- **WHEN** reviewers evaluate the change for deployment
- **THEN** they can trace each acceptance criterion to test evidence or an explicitly accepted exception
