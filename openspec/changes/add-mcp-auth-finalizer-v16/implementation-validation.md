# V16 Source Implementation Evidence

## State And Pair

Implemented under explicit approval in fix/mcp-v16-auth-finalizer, based on
Restaurant design 66a20e2 and maintenance version-16 c96d967. Companion TIX is
fix/mcp-v16-auth-composition, based on design 7225853.

Implementation commits 4a28064 (Restaurant) and 95db579 (TIX) were pushed and the
exact remote hashes verified before this documentation-only closure. Their tested
functional sources remain unchanged; no maintenance merge follows from the backup.

Neither installed app nor the active MCP runtime was changed. No site was
initialized, no business record created, no provider contacted and no role,
permission, credential, site configuration, cache, migration or service operation
performed. No maintenance merge or deployment. This evidence is isolated source
validation, not permission to install or activate either app's changes.

## Changes

- One separate internal auth hook after the unchanged PedidosYa authenticator.
- New integrations/auth_finalizer.py: optional list/tuple callbacks, complete
  shape/name/duplicate validation before resolution, ordered snapshot and once-per-
  entry invocation. Empty means no-op; callback errors propagate without dispatch.
- No whitelist, public route, direct TIX import or required-app dependency.
- Existing PedidosYa test fixture uses native v16 release_local before/after its
  context and resolves the bridge with empty callbacks for standalone regression.
- New isolated bridge tests. Production PedidosYa JWT code, routes, vendor/user
  validation, API receivers and response behavior are not edited.

No DocType, field, fixture, patch, migration, tax, price, stock, accounting, order,
channel setting or shared native permission changes are part of this patch.

## Actual Tests

Python 3.14.3, installed Frappe 16.55.2 / ERPNext 16.53.0, with isolated app import
origins verified. Tests use synthetic settings/JWTs/accounts and mocked DB/
receivers. Real networking and frappe.connect were blocked in the combined run;
no site, provider or queue was needed. No v15 test or dependency install.

| Restaurant suite | Passed |
| --- | ---: |
| integrations.pedidosya.test_auth_hook | 21 |
| integrations.test_auth_finalizer | 21 |
| **Restaurant subtotal** | **42** |

The original 21 tests now pass after fixture cleanup; the historical 21 setup
errors remain documented in validation.md and were not product/runtime failures.
JWT/path/verb/cmd/override/IP and 202/200/400 receiver contracts stay under test
with fakes, not real credentials or orders.

The coordinator's selected paired matrix passed **185 total, zero skips**:
Restaurant 42, existing TIX guard/policy/minimum-permission 63, new TIX composition
46, actual paired auth 12 and existing synthetic account operator 22. Do not add
individual/agent reruns to that total. It is not the entire app test suite.

The 12 paired cases import this actual bridge and PedidosYa authenticator and use
the native Frappe auth runner/set_user. OAuth/API-key lookup and IP rules are
test doubles; dispatch is a spy. They prove source composition and rejection
propagation, not full HTTP dispatch, a live channel or receiver-side effects.
The suite is optional without the companion app, but this acceptance run asserted
both import origins and executed all 12 without skipping.

## Review And Validation

Independent review found no material source issues in the guard, bridge, fixtures
or paired tests, while retaining the credential/IP-double and live-certification
limits. It did not independently execute the coordinator's matrix.

Both OpenSpec changes passed strict validation. Syntax/import checks passed for
all eight affected Python files, the 42/8 TIX catalog stayed unchanged, and all
three auth callables were absent from native whitelist/Guest method sets.
git diff --check passed. The final combined rerun blocked frappe.init in addition
to connect/networking and passed 185 cases with zero skips.

Graphify regenerated this app's 360 code files locally: 2669 nodes / 4877 edges,
with 75 zero-node source/metadata omissions reported. TIX was handled separately.
Code-only mode used no providers/installers/hooks; output/analysis were confirmed
ignored and unversioned. This graph is not complete metadata/security certification.

## Pending Operations And Reversal

Recheck effective auth/callback ordering and exact paired loaded versions before
installation/activation. Marker assignments must be inspected BEFORE code loads.
Private baseline/session/socket/job inventory, controller/read-subset audit,
formal external MCP v16 compatibility, pilot risk acceptance and exact rollout/
cache/process/account authorization remain open. Native All grants/warnings are
unchanged; source protection is not strict native least-privilege certification.

A missing final callback or later authenticator invalidates Guest-to-marked
coverage; no global ordinary-user denial masks it. The TIX pin protects the
identity observed by its early guard, not arbitrary trusted earlier/later code.
String lists alone do not certify execution, loaded code or process caches.

Before deployment, reversal is keeping installed sources/runtime untouched.
After a future activation, stop credential use before separately approved paired
recovery and drift checks. Do not remove the marker or restore only one app in
a live pair and assume broader native capabilities remain blocked.
