# Align Installed V16 MCP Sources

## Approval And Purpose

The owner authorized updating only installed TIX and Restaurant code to their
already integrated version-16 commits, followed by bounded read verification on
the existing approved v16 site. No new bench or site is created.

## Scope

Restaurant: c1333a8bb7d557e1eb8af27c5f3384e86e73f467 to
037c8a1dcb7b6ff968345658eab2da2834a5d6b0, using an exact detached checkout.
The matching change in the paired app records the other source pin. All five
authentication runtime files and their modes must remain identical. Only tests,
local operator utilities and documentation differ from the installed pair.
Restaurant's five minimarket design documents leave this checkout but remain
preserved in their original branch/history; do not delete that branch or history.

## Risk And Exclusions

Risk: high for an installed authentication-boundary update, despite identical
runtime blobs. No business API/DocType/fixture/patch/schema/tax change, native
permission write, service/cache operation, migration, explicit reload, channel or
external MCP update. Acceptance of inherited All risk is retained, not hidden.

## Acceptance

Validate scope and OpenSpec, preserve exact rollback pins and remote backups,
check preflight reads, update Restaurant before TIX, then verify fresh source
origins, 235 paired synthetic cases, 25 runner tests and bounded HTTP reads.
Report exact outcomes and limitations; no claim of universal worker coverage.
Document and push evidence branches without another maintenance merge.
