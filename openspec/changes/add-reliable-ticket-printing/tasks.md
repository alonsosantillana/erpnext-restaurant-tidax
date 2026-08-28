## 1. Specification and baseline

- [x] 1.1 Record Windows, HWB 0.13.0, printer mappings and permanent station assumptions.
- [x] 1.2 Define acknowledgements, ambiguous delivery and no-duplicate policy.
- [x] 1.3 Define ownership between silent_print and Restaurant Management.

## 2. silent_print transport

- [x] 2.1 Implement secure configuration and master-tab registration.
- [x] 2.2 Replace legacy PDF generation with the Frappe v15 API.
- [x] 2.3 Implement bounded WebSocket connection, queue and backoff.
- [x] 2.4 Normalize HWB 0.13.0 and 1.0.1 responses.
- [x] 2.5 Add transport and permission tests.

## 3. Restaurant queue and routing

- [x] 3.1 Add Restaurant Print Station, Route and Job metadata.
- [x] 3.2 Add company validation, leases, idempotency and lifecycle APIs.
- [x] 3.3 Add the permanent print-station page and status UI.
- [x] 3.4 Route precuenta and electronic invoice printing through the queue.
- [x] 3.5 Add auditable confirm-printed and discard actions for print incidents.
- [x] 3.6 Add an immediate, company-scoped station disconnect action.
- [ ] 3.7 Add optional ORDER and KITCHEN triggers for newly sent rounds.

## 4. Qualification

- [ ] 4.1 Add Python and browser-facing regression tests.
- [x] 4.2 Run migrate, build and static checks on v15.local.
- [ ] 4.3 Validate offline, rejection, acknowledgement and ambiguous scenarios.
- [x] 4.4 Execute a controlled physical print with POS-80-Series and HWB 0.13.0.
- [ ] 4.5 Record optional HWB 1.0.1 and ESC/POS follow-up validation.
