# Proposal

## Problem

The mobile API order access validator requires an authorized room for every
Table Order. Delivery and Pickup orders intentionally have no room, so the
controlled R8D POS preparation and native invoice submission fail before
fiscal, payment or invoice checks.

## Objective and Scope

Permit roomless Delivery/Pickup orders only when a billing caller explicitly
opts into off-premise access. Preserve company, POS Profile, order permission,
owner/exception and open-order checks. Keep the room restriction on Dine In
and on all existing non-billing mobile API calls. Coordinate the R8D caller
in TIX to use the opt-in.

## Exclusions

No change to invoicing amounts, tax, payment, series, fiscal payloads,
inventory, DocTypes, roles, fixtures, hooks or unrelated mobile endpoints.
No invoice or site operation is executed as part of this change.

## Impact and Acceptance

Risk: high, because authorization precedes a financial and fiscal action.
Delivery/Pickup billing may pass only for a roomless/tableless order in the
active company and POS Profile with existing native order permission. Dine In
with an unauthorized room, invalid off-premise context, and non-billing
off-premise calls remain rejected. Unit and MCP contracts pass before an
operator-run live preview; invoice submission remains a separate approval.
