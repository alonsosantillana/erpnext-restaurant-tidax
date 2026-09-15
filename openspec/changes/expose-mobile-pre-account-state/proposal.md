# Change: Expose pre-account state to Resto TIX Mobile

## Why

ERPNext already tracks and publishes table pre-account state, but the Mobile table contract does not include it or the configured presentation colors.

## Objective

Expose a minimal, permission-preserving representation of the existing ERPNext state for Mobile rendering.

## Scope

- Add normalized `pre_account_status` to accessible active-order summaries.
- Add the company-configured requested and outdated colors to the authenticated context.
- Reuse existing table access checks and synchronization events.

## Acceptance criteria

- Only `Requested`, `Outdated` or `null` is returned.
- No additional order becomes visible through the endpoint.
- Color configuration follows the active restaurant company.
