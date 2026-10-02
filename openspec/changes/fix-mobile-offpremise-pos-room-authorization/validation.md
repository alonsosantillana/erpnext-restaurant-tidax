# Validation

## Cause

R8D preparation for a roomless Delivery order was rejected with
`ORDER_NOT_ALLOWED: The requested order belongs to an unauthorized room`.
The native validator required a room for every Table Order, including
Delivery/Pickup. No token, invoice or payment was created by that attempt.

## Code checks

- Native mobile API tests: 26 passed.
- TIX R8D contracts: 12 passed.
- Full TIX MCP suite: 1,517 run, 87 skipped, no failures.
- Native validator bypass is opt-in and limited to roomless/tableless
  Delivery/Pickup. Other mobile callers retain their previous room check.
- Both OpenSpec changes pass strict Node 20 validation.
- Native company, POS Profile, order permission and open-order checks remain.

## Operator follow-up

Deploy matching `restaurant_management` and `tix` code, then repeat only
the R8D preparation for an authorized test order. Confirming the token,
recording POS payment and fiscal submission require separate operator approval.
No migrate is needed for this code-only fix. No live invoice was created here.
