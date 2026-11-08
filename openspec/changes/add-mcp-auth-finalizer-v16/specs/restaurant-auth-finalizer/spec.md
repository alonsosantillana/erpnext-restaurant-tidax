## ADDED Requirements

### Requirement: Optional internal finalizer after PedidosYa
Restaurant SHALL expose a separate internal native auth hook after its existing
PedidosYa authenticator, invoking callbacks from tix_mcp_read_auth_finalizers
without a direct TIX dependency, public endpoint or request-derived callback.

#### Scenario: Restaurant operates without a TIX callback
- **WHEN** the configured callback list is absent or empty
- **THEN** the bridge is a no-op and existing native authentication is preserved.

#### Scenario: A normal route is unrelated to PedidosYa
- **WHEN** the PedidosYa authenticator returns without selecting an identity
- **THEN** the separate bridge still runs later in the native chain.

### Requirement: Preserve failure and native authentication semantics
The bridge SHALL NOT authenticate a user itself, bypass native final auth/IP
validation, suppress a callback denial or run callbacks in an authenticator's
finally block.

#### Scenario: PedidosYa rejects an invalid JWT
- **WHEN** its existing authenticator raises an authentication error
- **THEN** neither the bridge nor business dispatch runs afterward.

#### Scenario: The MCP finalizer denies a late-selected restricted identity
- **WHEN** the callback rejects the final identity or request
- **THEN** native dispatch aborts without running a restaurant receiver.

### Requirement: Paired scope and deployment invariants remain explicit
The bridge SHALL be validated with its TIX companion on v16 using synthetic data
before any separately approved rollout. Effective chain/callback drift SHALL
invalidate certification, not trigger silent app reordering or global user denial.

#### Scenario: Paired source tests complete
- **WHEN** offline bridge, identity-transition and original PedidosYa tests pass
- **THEN** those results do not imply site installation or activation
- **AND** native role warnings and live session/socket/job review remain separate.

#### Scenario: A later identity-changing hook or missing callback is discovered
- **WHEN** deployment review no longer establishes final enforcement
- **THEN** activation or certified credential use stops pending review
- **AND** no universal fail-closed claim is made for that unreviewed chain.
