# Installed V16 Source Alignment Evidence

## Approval And Scope

Owner-approved code-only installation on the existing approved v16 site,
2026-11-09 (America/Lima). This evidence belongs to Restaurant; the paired app has
its own matching change. No new bench/site, migration, role write, channel or
external MCP update was authorized or performed.

The installed pair was clean and its remote maintenance pins matched before
alignment. All five authentication blobs/modes, and other operational application
files outside tests/operator utilities, were unchanged. Independent static review
confirmed this and the bounded recovery. Both dedicated specifications validated
strictly before checkout. The subsequent health-gate clarification was also
validated before application; no failed security/read gate was bypassed.

## Source And Recovery Pins

| App | Before | Installed target |
| --- | --- | --- |
| TIX | 41d8d21669ba9f149faac70d8b68fafcbff6fe80 | 7bf4e25249d1a99198875554a3345d9f969b8489 |
| Restaurant | c1333a8bb7d557e1eb8af27c5f3384e86e73f467 | 037c8a1dcb7b6ff968345658eab2da2834a5d6b0 |

Original source remains backed up in the pilot branches, whose upstream tips
were actually checked: TIX 19ac91c and Restaurant c3d5342 contain the original
installed commits. The five minimarket documents leaving Restaurant's checkout
remain in docs/minimarket-pos-coexistence-v16 at 9466ba8, also verified upstream.
No branch, history, unrelated user work or business data was deleted.

Procedure/evidence branches are separate from installation. The preparation
commits were pushed and actual remote hashes matched before source checkout:
TIX 8b03da24c5007166fa3fef97b0559dc4debf082f and Restaurant
c472c62b67f3a81dee0190a6c93f1d79bcbb26b4. Later evidence-only commits are not
installed targets and do not advance version-16. Final remote evidence hashes
are checked at delivery.

## Baseline And Diagnostic Deviation

The first baseline got guest ping 200, then its first authenticated projected
resource request returned the helper's suppressed OperatorError. No checkout
occurred. A separate single-request transport diagnostic then got the projected
table resource at HTTP 200 in 0.209 seconds, with one name-only row. No service,
cache, configuration or source change caused that later success; cause unknown.

The next baseline passed all seven required GET probes, but health timed out
at its 15-second socket bound. The four restaurant resource reads were checked
separately and all returned 200. The timeout is consistent with the previously
documented intermittent diagnostic, not a new observed authentication failure.

Before proceeding, the design explicitly separated this health diagnostic from
the mandatory source/auth/read gates: identical runtime blobs plus all seven GET
probes and all four business-resource reads were required. Independent review
confirmed no material technical blocker under those conditions. Health was not
marked passed by that decision; no timeout retry loop or restart was used.

## Application And Intermediate Check

Restaurant was checked clean and still at its original pin immediately before
checkout. It was aligned first, using git -c core.hooksPath=/dev/null checkout
--detach at its exact target. This command-scoped setting avoids unreviewed Git
automation without editing repository configuration. The checkout remained clean;
both auth files compared identical to the original source.

All seven required GET probes and all four restaurant reads passed in the
intermediate state. Health was intentionally not repeated at that checkpoint.
The external MCP source still resolved to 2561e60ccc200c732b1df007331a61b1b9324e21.

TIX was then rechecked clean and still at its original pin, aligned using the
same hook-disabled detached-checkout procedure, and checked clean afterwards.
Its hooks, guard and policy compared identical to the original blobs. Both
maintenance refs and the external MCP pin remained separate from these operations.

## Final Verification

The versioned offline runner was executed from installed TIX against installed
Restaurant, with Python -I -S -B, explicit bench/dependency roots and the existing
process-local filesystem/site/DB/Redis/network/subprocess safeguards. Result:
235 tests, zero failures/errors/skips/expected failures/protected IO attempts.
The installed runner's 25 separate stdlib self-tests passed with no skips.
Runtime reported Frappe 16.55.2 / ERPNext 16.54.0, bench Python 3.14.3.
Reruns are not additional unique coverage.

The final loopback-only HTTP check used the existing private connection only in
memory, no redirects/retries/audit POST and bounded response/time limits:

| GET probe | Final result |
| --- | --- |
| Guest ping | 200 |
| Restaurant Object, name only, limit one | 200 |
| Table Order, name only, limit one | 200 |
| Native identity route | 403, exact guard denial |
| Duplicate limit | 403, exact guard denial |
| Inert method-override header | 403, exact guard denial |
| Limit 101 | 403, exact guard denial |

Health returned HTTP 200 in 0.882 seconds, mapping count 40, overall warning.
The warning checks were controlled_actions and minimum_permissions: controlled
actions remain disabled, and the owner-accepted inherited All risk is retained.
This later success does not diagnose or fix the earlier intermittent timeout.

Company-filtered, minimally projected reads all returned HTTP 200:

| Section | Returned rows | Limit / interpretation |
| --- | --- | --- |
| Tables | 4 | cap 20, not saturated |
| Active reservations | 8 | Pending/Confirmed/Arrived/Seated; cap 20 |
| Recent table orders | 20 | cap saturated; sample, not total order count |
| Recent fulfillment | 12 | 5 Pickup, 7 Delivery; cap 20 |

Resource reads were ordered by modified desc when mapped, otherwise name desc,
following the existing MCP summary contract. No identifiers, customer/contact
data, addresses or response bodies were printed or copied into evidence.
The same counts were observed before, intermediate and after, but that is not a
database immutability certificate or an exhaustive count of restaurant history.

## Limits And Recovery

Both installed worktrees were clean at the targets after validation. No business
document, permission, setting, provider, database/Redis connection from synthetic
tests, migration, dependency, explicit service/reload or cache reset was changed.
Normal live GET processing is not claimed to be free of all internal cache/log
activity. No native MCP call or external-MCP restart/reload was performed.

The old activation receipts still pin older source commits by design and were
not edited or reused as proof of this source alignment. Runtime blob equality,
installed-origin synthetic tests and bounded live GETs are the actual evidence.
No universal long-lived worker/session/socket/POS certification is claimed.

No recovery was needed. If a later rollback is proposed, recheck concurrent
changes and use only the original guard-bearing source pins above; do not remove
the marker, go to pre-guard code or alter shared rights. Further operational
diagnostics, archival and any maintenance merge of this evidence need their own
scope; they are not implicit in this completed installation.
