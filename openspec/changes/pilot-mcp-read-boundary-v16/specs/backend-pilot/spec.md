## ADDED Requirements

### Requirement: Preserve The Existing Site During Bounded Backend Installation
The pilot SHALL install only the reviewed backend source for Restaurant, retaining
unrelated work, current settings, permissions and maintenance references.

#### Scenario: Reviewed Source Transfer
- **WHEN** the pilot candidate is prepared
- **THEN** its backend files match the reviewed source exactly
- **AND** unrelated backend files and documentation remain present

#### Scenario: Installation Precondition Fails
- **WHEN** a marker is already assigned, source drift exists or hook composition is unknown
- **THEN** installation stops without role/configuration/service changes

#### Scenario: Clean Unmarked Pilot
- **WHEN** the validated backed-up pair is installed on the existing v16 site
- **THEN** Restaurant precedes TIX in source installation, not in installed-app order
- **AND** ordinary GET checks run with bounded timeouts and no business mutations
- **AND** account activation, marked-account HTTP certification and maintenance merge remain separate
