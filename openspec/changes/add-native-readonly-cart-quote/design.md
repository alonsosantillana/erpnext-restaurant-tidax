# Design

Add quote_cart(cart, context) to restaurant_management.order_quote. Factor existing
calculation into a shared private function with unchanged quote_order behavior.
Cart validation excludes phone, promised time and notes, requires real customer,
and requires a real owned address for delivery; no generated defaults.

Preserve enabled user, company scope, applicable POS users/customer groups, native
record permissions, single currency, exact native price resolution, supported
tax-template/account constraints, rounding guards, and fail-closed unsupported
pricing. Existing quote_order validation remains strict and unchanged externally.

Cart output adds net_total and computed taxes_and_charges with ordinal,
rate, tax_amount and included_in_print_rate. Never expose descriptions, account heads, customer,
address contents, contact data, fingerprints or authorization receipts. Reuse
POSInvoice constructor and calculate_taxes_and_totals in memory only. Do not run
POS defaults, validate, save, insert, submit or hooks. Restore temporary flags.
No business/application persistence or quote caching is allowed; ordinary native
metadata/permission cache population is not claimed to be eliminated.

Tests use existing synthetic native fixtures with persistence/site/network guards;
add cart-specific input, calculation and authorization regressions. No live tests.
No schema/migration/data rollback. Revert paired dedicated source commits if later
deployed; merge/application is outside authorization. Base version-16 037c8a1.
Graphify consulted locally; quote nodes were absent in the older native graph;
source code is authoritative. TIX is the only new HTTP entry point.
