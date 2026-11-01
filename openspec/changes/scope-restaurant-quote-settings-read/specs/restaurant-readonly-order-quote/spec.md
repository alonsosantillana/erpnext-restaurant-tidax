## ADDED Requirements

### Requirement: Quote configuration SHALL use a fixed authorized projection
The internal quote SHALL read only the fixed current-company/POS configuration
fields it needs, without generic Settings document/customer access or new grants.

#### Scenario: Unrelated default customer is restricted
- **WHEN** the principal may read the selected configuration fields and bound scope
- **THEN** quoting does not fetch default_customer or other unrelated Settings data
- **AND** direct Customer/Address/full Settings permissions remain unchanged.

#### Scenario: Selected fields or row are not authorized
- **WHEN** role, read permlevel, owner, Settings-name or relevant Link scope fails
- **THEN** the projection rejects without shared-document or owner scope rescue.

### Requirement: Projection support SHALL fail closed for unsupported policy and binding
The projection SHALL retain actor/company/readable POS authority and reject
ambiguous settings or unsupported custom authorization policies.

#### Scenario: Unknown authorization extension is configured
- **WHEN** an applicable permission/query hook, Permission Query Server Script or Settings class override is present
- **THEN** quoting rejects rather than ignoring it or guessing missing field values.

#### Scenario: Settings metadata sorts by an unrelated private field
- **WHEN** effective Settings metadata requests sorting by an omitted customer field
- **THEN** the projection query uses fixed name ascending ordering instead.

#### Scenario: Persisted Settings profile differs from the authorized profile
- **WHEN** a missing, foreign, blank or alternate POS binding is selected
- **THEN** the quote is unavailable and no alternate company/profile is substituted.

#### Scenario: Actor or restrictions change between reads
- **WHEN** another actor quotes or effective permissions are revoked
- **THEN** projection authorization is freshly evaluated and old access is not reused.
