## ADDED Requirements

### Requirement: Preserve The Active Read Boundary During Source Alignment
The installed update SHALL use the exact approved v16 pair while preserving
authentication runtime blobs, native permissions and separately pinned MCP code.

#### Scenario: Clean Approved Source Pair
- **WHEN** remote pins, source diffs and baseline reads match the approved scope
- **THEN** Restaurant is aligned before TIX without moving maintenance refs
- **AND** no migration, service operation, role write or business action occurs

#### Scenario: Concurrent Drift Or Failed Read
- **WHEN** an installed worktree is dirty, source differs or a required read fails
- **THEN** the update stops with evidence and no destructive cleanup
- **AND** any recovery retains the guard and original safe source pins

### Requirement: Report Bounded Verification Without Exposing Business Data
The verification SHALL use bounded local GETs and explicit installed-origin
offline tests, preserving inherited-rights warnings and certification limits.

#### Scenario: Completed Source Alignment
- **WHEN** the exact source pair is installed
- **THEN** offline tests and live read/denial probes report actual outcomes
- **AND** credentials, account identities and business rows are not emitted
- **AND** source installation is distinguished from worker or external-MCP deployment
