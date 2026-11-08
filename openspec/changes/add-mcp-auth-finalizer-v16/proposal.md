# Optional V16 MCP Authentication Finalizer

## Status And Problem

Design only, pending explicit authorization for the additional Restaurant source
change and paired tests. Nothing is implemented, installed or enabled here.
The owner selected Frappe / ERPNext 16 exclusively for this work.

The existing native site order places TIX authentication before Restaurant's
PedidosYa authenticator. A restricted MCP identity selected by a later hook needs
a final policy check before dispatch. Frappe 16.55.2 exposes no universal app hook
between completion of the native auth-hook loop and all REST/RPC dispatch.
Reordering apps or changing core would have broader impact and is not proposed.

## Scope

Add a separate native auth hook after the existing PedidosYa hook. It invokes
callbacks registered in tix_mcp_read_auth_finalizers, with no direct TIX import,
required app, new public endpoint, account selection or JWT implementation.
An absent callback list is a no-op. Denial/errors must never become a successful
authentication or business dispatch.

Planned functional files after approval: restaurant_management/hooks.py,
restaurant_management/integrations/auth_finalizer.py and focused tests, including
necessary test-hook-map and native v16 local-context-cleanup updates to existing
PedidosYa regressions. The unchanged baseline has 21 setup errors at the obsolete
cleanup call; see validation.md. It is not a claim of a live integration failure.
Companion TIX change: compose-mcp-reader-auth-v16 in alonsosantillana/tix.
Restaurant base: version-16 c96d967; the installed documentation worktree remains
unchanged. No dependency on that unrelated documentation branch is introduced.

## Risk, Exclusions And Acceptance

Risk is high because authentication is shared infrastructure. The bridge must
run on every route after PedidosYa, not inside its route filter or a finally
block. Existing JWT validation, integration-user selection, routes, native IP
checks and 202/200/400 API contracts must remain unchanged for ordinary identities.

No new DocTypes, fields, permissions, roles, fixtures, patches, migration,
channel activation, order/stock/accounting/tax changes, external request, core
modification or package installation. Source approval does not authorize live
configuration, caches, services, marker assignment, main merge or deployment.

Acceptance requires paired synthetic v16 tests of the observed chain and identity
transitions, unchanged standalone Restaurant behavior, no real IO and independent
review. Effective hook/callback ordering and loaded sources remain deployment
invariants. No claim of universal protection against arbitrary later trusted
authenticators or previously open sessions/sockets/jobs is made.
