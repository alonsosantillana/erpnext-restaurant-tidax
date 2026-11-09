## ADDED Requirements

### Requirement: Retain Reproducible Scoped V16 Backend Tests
The candidate pair SHALL retain only the reviewed MCP runtime scope and its
portable focused test suite without changing the installed applications.

#### Scenario: Reproducible Offline Run
- **WHEN** the runner receives explicit candidate roots under the existing v16 runtime
- **THEN** imports resolve to those roots and protected IO is blocked before suite loading
- **AND** the exact scoped manifest runs with no skips or hidden missing modules
- **AND** attempted protected IO or test failures produce a nonzero result

#### Scenario: Unrelated Or Missing Source
- **WHEN** a paired module is missing, a source origin differs or the count drifts
- **THEN** validation fails without connecting to a site or executing business actions

### Requirement: Preserve Scope And Pending Approval Gates
The preparation SHALL preserve maintenance references, installed sources and
existing minimarket work while retaining native permission warnings.

#### Scenario: Scoped Candidate Prepared
- **WHEN** the branches are backed up for review
- **THEN** Restaurant excludes unrelated minimarket documents and their ancestry
- **AND** no site migration, permission write, service operation or principal merge occurs
- **AND** native inherited-rights acceptance remains an explicit separate gate
