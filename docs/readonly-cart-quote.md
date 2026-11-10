# Native Read-Only Cart Quote

`restaurant_management.restaurant_management.order_quote.quote_cart(cart, context)`
is an internal price-only adapter for Frappe/ERPNext v16. TIX provides the bounded
authenticated GET/MCP entry point. This function is not whitelisted and does not
grant order-admission authority.

The cart has service_type (Pickup or Delivery), a real readable customer, and
1-50 distinct item_code/qty rows (integer quantities 1-1000). Delivery requires
an existing readable address owned by that customer. Pickup forbids address.
Contacts, schedules, notes, routing overrides and caller prices are rejected.

Context remains server-resolved: company, POS profile, selling price list,
profile modification and currency. Existing native authorization, applicable
profile users, customer/item groups, settings, price ambiguity, address ownership,
single currency and supported tax-template/account guards all remain in force.
Prices are current-date, not promised-time or future-date pricing.

`quote_order` retains its original contact/time validation and exact legacy output
including fingerprint. Both entries share one calculation: native POSInvoice is
constructed and taxed in memory, without defaults, validate, hooks or persistence.
Cart output adds net_total and at most ten ordinal tax/charge rows without accounts,
descriptions, customer/address data or fingerprints. Amounts are decimal strings.
The `tax` field includes configured service charges. Inclusive amounts must not be
added twice. Delivery fee uses the configured native price and is included once.

Unsupported pricing raises QuoteUnavailable. Do not substitute guessed totals,
invented client data or zero-price fallbacks. This snapshot cannot replace fresh
review, consent and human approval before any future order creation.

No business/application records, quote caches, stock, payment or provider calls
are written. Framework metadata/permission cache population is not eliminated.
No schema, permissions, fixtures, patches or migrations are required. Apply the
paired TIX/native commits only with a separately approved deployment; revert them
together if necessary. Offline fixtures are not acceptance of installed-site data.

Tests use the actual v16 price/tax engine with synthetic reads and traps for
document/DB writes, network, jobs, email and realtime. The shared test fixture uses
the native v16 Local interface and metadata shape; the reviewed inclusive-tax
expectation for its synthetic cart is 38.14, not the older engine's 38.13.
