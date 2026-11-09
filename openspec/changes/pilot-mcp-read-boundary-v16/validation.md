# Bounded V16 Backend Pilot Evidence: Restaurant

## Source And State

Applied in the owner-approved backend-only pilot. The first candidate commit
recorded preparation before installation; the outcomes below supersede that
initial state. The paired TIX candidate derives from installed
9d281ed0c9f7207f49e75d0055188a1d3eef79dc, and Restaurant from installed
9466ba8190d71e144505e22c06b66d8ab59ea98a. The latter's five existing minimarket
coexistence documents are preserved. Maintenance refs and external MCP are unchanged.

Only three TIX backend files (hooks, guard, policy) match the reviewed TIX
source ddba9776957cd5580067e83cdc883ffa431cd58b, and two Restaurant files
(hooks and finalizer) match 5211f6eae12f86c6c292bc08829a5168fa30745c.
All five byte comparisons passed. README/OpenSpec documentation accompanies the
pilot; stale descriptive OpenSpec context now targets v16, not historical v15.
No business controller, DocType, fixture, patch or package runtime is changed.

## Offline Verification

Frappe 16.55.2, ERPNext 16.53.0, Python 3.14.3: 185 focused tests passed with zero
skips against the new backend import origins. Fixtures are taken explicitly from
the reviewed TIX/Restaurant candidates, not silently from the installed checkouts.
The original Restaurant test fixture is not part of this five-file deployment.
Socket connections, frappe.init and frappe.connect were blocked in the synthetic
run. Tests do not invoke real OAuth/API-key/IP providers or business dispatch.

The first relocated harness run executed 185 with one provenance assertion
failure: the composition fixture's ROOT still referred to its old review checkout.
Only that fixture expectation was pointed at the new asserted candidate root;
no production code, test behavior or expected authorization result was changed.
The corrected run passed all 185. Do not add reruns or the initial failure to
unique coverage counts. This is focused coverage, not full app/POS certification.

Strict OpenSpec and diff checks passed before source transfer. Existing per-app
Graphify/source review supports the same previously reviewed architecture; no
new graph, provider, dependency or mixed-app artifact is required or published.

## Protected Preflight And Ordinary HTTP Baseline

A temporary local inventory used a READ ONLY transaction and SQL/Redis write
command guards, rollback and context destruction. Module-map cache generation
was skipped for the diagnostic only. It did not change installed configuration.

- Current installed source auth chain: PedidosYa only; finalizers empty.
- Marker Role names and Has Role rows, including normalized names, profiles and
  orphan rows: zero. All cached role lists also contained zero markers.
- Current app order is TIX then Restaurant. Developer mode is enabled and the
  persisted app-hooks cache is absent. Auth functions resolve without invocation.
- Projected final chain: TIX guard, PedidosYa, terminal Restaurant bridge;
  exactly one TIX finalizer callback. Fresh-process source is not worker proof.

A stateless loopback HTTP helper consumed the existing private connection
credentials only in memory. Static GET routes, bounded timeouts, no redirects,
no retry and metadata-only outputs were used. No business payload, identity or
secret was logged/copied into these repositories.

- Existing MCP health GET: timed out at five seconds, before installation.
- Public HEAD login: timed out at five seconds, before installation.
- Public GET ping: HTTP 200, first byte approximately 0.103 seconds.
- Authenticated Restaurant Object list: HTTP 200, names only, limit one.
- Authenticated Table Order list: HTTP 200, names only, limit one.

The two resource reads were checked separately with a ten-second bound; this was
not an automatic health retry. Health/login timeouts remain a pre-existing open
diagnostic issue, not a claim that the whole server is unavailable. Health also
builds action-readiness metadata; no health implementation change is in scope.
No restart or configuration change is justified by the healthy minimal reads.

## Rollout Gate And Limits

Independent review found no material defect in the exact five backend blobs,
conditional on clean backed-up source, zero database/cached markers, known hook
composition and intermediate verification before the second checkout. That
review did not execute the reported tests or read the live inventory itself.

The pilot may proceed only with the same preconditions freshly rechecked.
Restaurant is installed first (bridge present, no callbacks), then TIX (exact
single callback resolvable). Do not change installed-app order. Preserve both
old source commits and stop if source drifts, callbacks fail or ordinary reads
regress. Any code-only recovery must check concurrent changes and markers first.

Installation outcome, candidate commit hashes and remote verification appear
below. Account activation, marked-account HTTP denial,
loaded-worker enforcement, Redis sessions/realtime sockets, inherited All rights
and general external-package v16 acceptance remain separate unpassed gates.
No role, grant, settings/cache edit, migration, service command, channel activation,
provider contact, business action or maintenance merge is part of this pilot.

## Applied Pair And Post-Checks

Before installation, both branches were pushed to their respective upstreams and
ls-remote matched the exact commits:
- TIX: 41d8d21669ba9f149faac70d8b68fafcbff6fe80.
- Restaurant: c1333a8bb7d557e1eb8af27c5f3384e86e73f467.

The fresh pre-install inventory additionally checked cached role lists, import
origins for both installed apps and auth callables, and a fingerprint of the
complete installed-app order. All marker counts were zero; original checkouts
were clean and still at their recorded bases.

1. Installed Restaurant at the pinned candidate commit using a detached checkout,
   leaving its original documentation branch intact. The intermediate read-only
   inventory found PedidosYa then the bridge, no finalizer callback, no markers
   in roles/assignments/cache, and the same complete app order. Auth functions
   resolved from installed files. Both ordinary resource GETs returned HTTP 200.
2. Rechecked clean installed sources and their exact revisions, then installed TIX
   at its pinned candidate commit using a detached checkout. No main ref advanced.
3. The final read-only inventory found TIX guard, PedidosYa, terminal bridge and
   exactly one resolvable TIX finalizer. Database/cached marker counts remained
   zero, imports pointed at installed apps and the full app-order fingerprint
   matched before/intermediate/after.
4. Both authenticated resource GETs again returned HTTP 200, one projected name
   at most per response. Ten seconds was the socket timeout, not a complete
   operation deadline. No health retry or denial/action probe was sent.

Installed app worktrees are clean and remain pinned to the two commits above.
The TIX maintenance ref remains 9d281ed0c9f7207f49e75d0055188a1d3eef79dc;
Restaurant maintenance remains c96d9674ca448808debaa16afce6c3671d33f042,
and its documentation branch remains 9466ba8190d71e144505e22c06b66d8ab59ea98a.
The five minimarket documents compare unchanged with the original installed base.
The external MCP remains on its prior pinned source 2561e60; no connection reset
or package installation was performed.

These are applied-source, fresh-process hook and ordinary HTTP availability
checks. They do not prove finalizer execution in every long-lived worker, an
unobserved automatic reload, ordinary human-account UI behavior, marked-account
denial or pilot security acceptance. No explicit restart, cache invalidation,
migration, role/grant change or business write was executed. Health/login
timeouts were observed before source installation and remain unresolved.
