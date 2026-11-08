# Optional Terminal Authentication Bridge

The paired source implementation is approved and completed in isolated branches.
Read [implementation-validation.md](implementation-validation.md) for actual
results. The rollout gates below remain pending; source approval is not deployment.

## Placement And Ownership

Register restaurant_management.integrations.auth_finalizer.authenticate_request
as a separate auth_hooks entry immediately after
restaurant_management.integrations.pedidosya.auth.authenticate_request.
The proposed effective observed-site chain is TIX early guard, PedidosYa, bridge.
Do not change installed-app order or mutate the runtime cached hooks list.

The new internal callable reads tix_mcp_read_auth_finalizers through native
frappe.get_hooks and invokes its validated callback list through frappe.get_attr.
It is not whitelisted. It takes no request-derived callback name, URL, method,
account or authorization decision. False return values are not authorization;
the owning callback must raise to deny, like native auth_hooks.

Without callbacks, return without importing TIX, querying business documents,
inspecting credentials, authenticating anyone, writing data or logging identity.
With callbacks, invoke only the configured entries in order, once. Never catch
an authentication/permission denial and continue. Do not add the call in a
finally block: an earlier PedidosYa failure must abort normally.

TIX owns the exact accepted composition, marker selection and final request
policy, not Restaurant. The initial reviewed profile registers exactly one TIX
callback. The companion design is openspec/changes/compose-mcp-reader-auth-v16/
design.md in alonsosantillana/tix. TIX retains its unique native early hook and
terminal standalone mode, private request provenance and initially marked pin.
The final callback must check marked-to-unmarked switches as well as late
Guest/ordinary-to-marked authentication. It must not trust form_dict, session or
local.cache to retain the pin because native set_user resets mutable state.

## Native Behavior Preserved

The existing PedidosYa source authenticator remains unchanged: exact inbound
routes/verbs, remote vendor lookup, enabled nonstandard integration user,
configured JWT algorithms/claims, preserved form_dict and native IP validation.
Only its test fixture's native-hook map and context cleanup need adaptation.
The unchanged baseline fails at frappe.local.__release_local__, which is absent
on v16. Plan to use frappe.utils.local.release_local(frappe.local) through
addCleanup, not patch the framework or the production authenticator. Register
cleanup safely before test setup can fail. All vendor/credential lookups and
receivers remain test doubles. See validation.md for the actual failed baseline.

No TIX dependency is added to required_apps or install hooks. Restaurant alone,
without a callback, must still pass its original native-auth tests. The bridge
must also run for non-PedidosYa paths, where the existing authenticator returns
early. This is why a separate native hook is needed.

Native final auth/IP validation still runs after auth_hooks. The bridge neither
replaces those checks nor claims that authentication has already completed every
framework step. It must not execute a business callback/receiver as a test of
whether authentication was accepted.

## Invariants And Limits

The terminal bridge contract only holds when effective hooks and loaded paired
sources are reviewed. A later authenticator, missing final callback, duplicate
bridge or incompatible TIX revision invalidates certification. TIX may deny a
known marked request on unsupported composition, but ordinary accounts must not
be globally denied as a workaround. A pin alone cannot secure a late identity
when the required final check no longer executes. Stop activation/credential
certification on drift; do not hide that operational limit.

An app hook is trusted Python; this proposal cannot secure deliberately malicious
server code, retroactively close sockets, stop running jobs or suppress all
framework authentication/security logging. It does not revoke inherited native
All rights or change the permission diagnostic's noncompliance result.

## Files And Data

- hooks.py: one additional internal native auth hook, preserving existing entries.
- integrations/auth_finalizer.py: optional callback bridge only.
- integrations/test_auth_finalizer.py: no-DB/no-network bridge/paired regressions.
- integrations/pedidosya/test_auth_hook.py: native v16 cleanup and test resolution
  updates to retain existing auth contracts with the bridge registered.
- Documentation and this OpenSpec change: exact evidence and pending operations.

DocTypes, fields, permission rows, SQL/data changes, fixtures, patches, migrations,
stock, pricing, taxes, series, payment and channel settings: not applicable.
No provider API, JWT secret from a site, user credential or real order is needed.

## Validation Plan

Use only installed Frappe 16.55.2 with isolated app imports asserted. Do not
initialize/connect a site. Replace DB/credential lookups and receivers with fakes;
block sockets, queues and actual business mutations. Use native validate_auth or
validate_auth_via_hooks and a dispatch spy, not an imitation auth pipeline.

1. Restaurant standalone with empty callbacks: ordinary/Guest/native requests
   and all existing PedidosYa JWT/path/verb/cmd/override/IP cases unchanged.
2. Bridge executes after a successful authenticator on every route; it does not
   run after an earlier authentication exception and never invokes a receiver.
3. TIX + PedidosYa + bridge: bounded allowed reads pass normal native checks;
   marked POSTs/aliases/auxiliary operations are denied before dispatch.
4. Initially marked to ordinary/Guest/another marked identity denies; initially
   Guest/ordinary to marked gets full final validation with valid early context.
5. Native TIX terminal order remains supported without premature finalization.
6. Missing/malformed/duplicate callbacks, missing bridge, extra later hook,
   forged/reentrant/stale request state and mutated request are covered with
   explicit boundaries; do not claim detection that the code does not perform.
7. Verify no public endpoint, direct TIX import, app/role/permission mutation,
   cached-list editing, network/provider contact or real business record.

Record actual results only after implementation approval. Graphify's existing
local PedidosYa relations were consulted without providers or query logging and
confirmed against source; no graph regeneration was necessary for design only.

## Rollout And Reversal

This design does not authorize installed source updates. Before any future
deployment, approve exact paired TIX/Restaurant commits, marker assignments,
effective auth/callback chain, controllers, read subset, private baseline and
sessions/sockets/jobs. Installation, cache/process operations, role changes and
main merges each remain outside source-only authorization.

Before deployment, reversal is leaving the existing installed sources untouched.
After future activation, stop credential use before approved paired code/account
recovery and revalidate drift. Removing a marker restores broader native rights;
do not roll back one app in a live mixed pair and presume the other still protects it.
