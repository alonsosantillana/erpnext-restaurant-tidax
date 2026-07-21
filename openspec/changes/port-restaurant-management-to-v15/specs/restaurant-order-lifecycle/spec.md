## ADDED Requirements

### Requirement: Valid order item state transitions
The system SHALL enforce a single server-side transition model for Order Entry Item states and SHALL prevent transitions out of terminal states except through an explicitly authorized recovery action.

#### Scenario: Normal kitchen progression
- **WHEN** an authorized user advances an item through Attending, Sent, Processing, Completed, Delivering and Delivered
- **THEN** each accepted transition records the resulting state and relevant timing exactly once

#### Scenario: Invalid regression
- **WHEN** a caller attempts to move a Delivered or Invoiced item back to an earlier state without an authorized recovery action
- **THEN** the server rejects the transition and retains the terminal state

### Requirement: Atomic order mutations
Creating, editing, dividing, transferring, sending, deleting or invoicing an order MUST be atomic within the request transaction.

#### Scenario: Successful split
- **WHEN** an authorized user divides valid quantities into a second order
- **THEN** both orders and all child quantities are persisted consistently without duplicate identifiers

#### Scenario: Failure during split
- **WHEN** validation or persistence fails after the split begins
- **THEN** neither order is partially changed and no explicit internal commit prevents rollback

### Requirement: Safe deletion
The system SHALL block deletion of an order containing items that passed the configured cancellable state and SHALL NOT clear child rows before evaluating the rule.

#### Scenario: Delete untouched order
- **WHEN** an authorized user deletes an order containing only cancellable items
- **THEN** the order and children are removed through Frappe document lifecycle hooks

#### Scenario: Delete sent order
- **WHEN** a user attempts to delete an order containing a Sent, Processing, Completed, Delivered or Invoiced item
- **THEN** deletion is rejected and all order items remain unchanged

### Requirement: Document lifecycle integrity
Table Order MUST use a documented Frappe document lifecycle and MUST NOT update `docstatus` directly.

#### Scenario: Invoice completes an order
- **WHEN** a POS Invoice is submitted and linked successfully
- **THEN** Table Order reaches its final state using the selected lifecycle and runs all applicable validation and event hooks

#### Scenario: Invoice submission fails
- **WHEN** POS Invoice validation or submission fails
- **THEN** Table Order remains open and no invoice link or final `docstatus` is persisted

### Requirement: Concurrency control
The server SHALL detect conflicting mutations to the same table or order and SHALL preserve one authoritative state.

#### Scenario: Two users edit the same order
- **WHEN** two clients submit incompatible changes based on the same earlier version
- **THEN** at most one mutation succeeds and the other client is instructed to reload current state

#### Scenario: Realtime update
- **WHEN** a transaction commits successfully
- **THEN** relevant clients receive a realtime notification and reload or reconcile against persisted server state

### Requirement: Non-destructive scheduled maintenance
Scheduled jobs SHALL operate only on explicitly eligible non-terminal records and MUST preserve Delivered, Invoiced, cancelled and otherwise final states.

#### Scenario: Daily maintenance runs
- **WHEN** the scheduler evaluates orders from a previous day
- **THEN** it updates only records meeting the documented expiry rule and records the action without rewriting unrelated states

### Requirement: Integrated production-center views
Each Production Center SHALL provide inline Commands, Dish Consolidation and Attended Orders views scoped to the center's configured item groups and status transitions, without opening secondary browser windows.

#### Scenario: Switch production view
- **WHEN** an authorized kitchen user selects another production view
- **THEN** the selected view replaces the current content inside the same Production Center and displays its current count

#### Scenario: Realtime production update
- **WHEN** an order is sent or a kitchen command changes state and the transaction commits
- **THEN** every open instance of the affected Production Center reconciles its active view and all view counters against persisted server data

#### Scenario: Realtime update while hidden
- **WHEN** an update arrives while the Production Center browser tab is hidden
- **THEN** the client marks the view as stale and reconciles immediately when the tab becomes visible

#### Scenario: Atomic command transition
- **WHEN** an authorized kitchen user starts or completes a command whose items still share the expected state
- **THEN** all selected items advance through the configured server-side transition in one transaction and timing is recorded once

#### Scenario: Individual dish transition
- **WHEN** an authorized kitchen user starts or completes one dish inside a command
- **THEN** only that dish advances, every dish retains its own visible state, and all dishes remain grouped in the same order round until the entire command is attended

#### Scenario: Advance lagging dishes in a mixed command
- **WHEN** a kitchen user applies the command-level action while its dishes have mixed states
- **THEN** only the dishes in the earliest transitionable state advance one step so already advanced dishes are not changed again

#### Scenario: Daily production control
- **WHEN** a kitchen user opens Dish Consolidation or Attended Orders
- **THEN** the views include the complete current calendar day, using an inclusive start and exclusive next-day boundary, consolidation separates pending, in-preparation and completed quantities, and Attended Orders lists the newest command first

#### Scenario: Conflicting command transition
- **WHEN** another client already changed any selected item or an item is outside the Production Center scope
- **THEN** the server rejects the entire command transition and the client reloads authoritative state

### Requirement: Auditable production timing
The system SHALL snapshot an optional preparation target when a dish is sent, record immutable first-transition timestamps and actors for preparation and completion, and calculate waiting, preparation and total durations without relying on the mutable document modification timestamp.

#### Scenario: Resolve preparation target
- **WHEN** a dish is sent to production
- **THEN** its target uses the positive Item value first, otherwise the positive direct Item Group value, otherwise remains without a target, and the resolved value and source are stored on the order item

#### Scenario: Record timing transitions
- **WHEN** a dish first enters Processing and later Completed
- **THEN** the system records the corresponding timestamps and users once and stores waiting, preparation and total durations in minutes

#### Scenario: Compact production timing indicators
- **WHEN** a user views Commands, Dish Consolidation or Attended Orders
- **THEN** the primary view shows one compact timing indicator and exposes exact timestamps, durations, target, variance and source on demand

#### Scenario: Timing performance thresholds
- **WHEN** an actual preparation time is compared with a positive target
- **THEN** below 80 percent is on time, 80 through 100 percent is near the limit, and above 100 percent is over target

#### Scenario: Comparable daily preparation averages
- **WHEN** Dish Consolidation calculates the current-day average preparation time and target for a dish
- **THEN** both averages are quantity-weighted and use only completed dishes, excluding pending and in-preparation dishes from the comparison
