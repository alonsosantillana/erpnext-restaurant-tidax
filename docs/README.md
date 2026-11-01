# Documentation

## Restaurant Interfaces

- [Internal read-only order quotes](readonly-order-quotes.md): supported pricing,
  scoped configuration authorization and safe validation boundaries.
- [Mobile waiter application proposal](mobile_waiter_app.md).
- [Mobile API contract](openapi/resto-tix-v1.yaml).
- [PedidosYa integration](pedidosya-integration.md).

## Compatibility And Safety

- [Test safety](test-safety.md): never run destructive ERPNext tests on an
  operational site.
- [Frappe/ERPNext v15 baseline](v15-baseline.md).
- [v15 qualification](v15-qualification.md).
- [Local per-app Graphify](graphify.md).

OpenSpec changes retain the requirements, design, exact validation and pending
acceptance for each task. Documentation is not an authorization to change a site,
deploy code or activate a channel. Shared operational rules live in the parent
bench's AGENTS.md and referenced agent guides when that bench is available.
