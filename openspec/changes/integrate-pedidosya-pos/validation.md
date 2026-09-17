# Validation

## Completed

- Python syntax: `python3 -m py_compile` passed for the integration, DocType controllers, fulfillment and hooks.
- JavaScript syntax: `node --check` passed for the PedidosYa Order form controller.
- JSON metadata: all three new DocTypes and the modified fulfillment DocType parse successfully.
- Unit tests: 23 tests pass for parsing, delivery modes/fees, mapping, JWT validation, callback URL security, sequential and concurrent idempotency, token reuse, test orders, atomic rollback and automatic acceptance.
- Whitespace: `git diff --check` passed.
- OpenSpec strict validation: `openspec validate integrate-pedidosya-pos --strict` passed using the locally installed Node.js `v20.20.2` runtime.
- Graphify: regenerated locally with `--code-only`; the final graph contains 2,988 nodes, 4,603 edges and 342 communities. It connects the API to the service/parser/client and fulfillment to the prepared callback. Generated files remain ignored.

## Runtime note

The default shell runtime remains Node.js `v18.20.8`. OpenSpec was invoked with the existing local Node.js `v20.20.2` binary through a command-scoped `PATH`; no global Node.js installation or default was changed.

## Deferred until staging credentials and deployment authorization

- Full Frappe regression for `Restaurant Fulfillment` and `Table Order`. It must run on a disposable site; the server currently has only the operational `v15.local` site and creating another site requires MariaDB administrative credentials. The destructive runner was not invoked against the operational site.
- Frappe migration and database-backed regression tests.
- End-to-end dispatch/callback tests against Delivery Hero staging.
- Reverse-proxy aliases for the literal Delivery Hero path contract, if required during onboarding.
- Production activation and live credentials.
