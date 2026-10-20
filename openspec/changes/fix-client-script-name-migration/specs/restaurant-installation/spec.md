## ADDED Requirements

### Requirement: Named room-permissions Client Script

Restaurant setup SHALL name a new POS Profile room-permissions Client Script
before inserting it, satisfying Frappe v15 Prompt naming. Existing matching
scripts SHALL retain their names, and repeated setup SHALL reuse them.

#### Scenario: Script is absent

- **WHEN** setup finds no matching room-permissions Client Script
- **THEN** it inserts the script named Restaurant POS Profile Room Permissions
- **AND** the name SHALL be assigned before the Prompt naming check

#### Scenario: Script already exists

- **WHEN** setup finds a matching POS Profile Form script
- **THEN** it updates that document without changing its name
- **AND** it SHALL NOT insert another Client Script

#### Scenario: Setup runs again

- **WHEN** setup runs after creating the room-permissions script
- **THEN** the existing script SHALL be reused
- **AND** no duplicate SHALL be created

#### Scenario: Legacy scripts remain disabled

- **WHEN** setup finds legacy POS Profile Form scripts containing new DeskForm
- **THEN** it SHALL continue disabling those scripts
- **AND** unrelated scripts SHALL NOT be disabled by this operation
