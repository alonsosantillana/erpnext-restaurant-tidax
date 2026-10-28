# Design

## Architecture And Boundaries

The sole new internal entrypoint is `order_quote.quote_order(proposal, context)`.
No whitelist decorator or caller-supplied rates/discounts/authority is added.
Use native restaurant company resolution and the original bound POS profile;
never replace it with the reviewing human's default POS. Verify enabled
System User, document-level read permissions, exact company/profile/list,
profile modification evidence and current actor applicability, enabled services,
active customer and a linked
Delivery address. Pickup must have no address. Reject malformed/big carts,
duplicates, serial/batch/variant/asset/template products and non-stock UOMs.

The first supported subset requires transaction currency = POS currency = list
currency = company currency. FX, including local FX, is deliberately unsupported
until separately certified; no get_exchange_rate fallback is imported. Read
prices through ERPNext get_price_list_rate_for, after checking permission-aware
candidate evidence for ambiguity, currency, validity, UOM and packing limits.
Reject enabled selling Pricing Rules and Sales Tax Rules conservatively instead
of silently ignoring their effects. Reject item or ancestor Item Group taxes,
customer/address/profile tax categories and other unsupported pricing inputs.

Delivery requires an explicitly configured non-stock fee item with its own
valid positive price, appended exactly once; it cannot appear as a cart item.
Pickup never appends it. Free or manually entered delivery charges require
handoff in this subset. No fee is inferred from untrusted proposal data.

Create an unsaved native POSInvoice instance from explicit safe fields, without
frappe.new_doc default-loading, set_missing_values, validate or any run_method.
Invoke ERPNext calculate_taxes_and_totals directly once for the entire cart.
Only explicit enabled same-company Sales Taxes and Charges Template rows of
type On Net Total, nonnegative bounded rates and non-group tax accounts are
accepted. Profile posa_tax_inclusive is authoritative, as in native TableOrder.
Reject item tax overrides rather than omitting them. Restore native tax engine
request-local flags on success or failure. Reject changed rates, unsupported
rounding, invalid/oversized monetary output and missing tax evidence.

Return exactly currency, lines(item_code, qty, rate, amount), tax, total,
delivery_fee, native_fingerprint. Product lines exclude the separate fee;
fee is the native fee line amount (inclusive if configured), tax is native
total_taxes_and_charges, total is native grand_total including fee. For inclusive
tax, line amounts already include tax, so consumers must not add tax again.
Fingerprint is SHA-256 of deterministic proposal/context/configuration/input
evidence and native result, no personal data returned. Maximum 120 safe chars.

## Affected Files And Runtime

- New `restaurant_management/restaurant_management/order_quote.py`.
- New `restaurant_management/restaurant_management/test_order_quote.py`.
- This dedicated OpenSpec change. No other source, JS, hooks, DocTypes,
  permissions, reports, fixtures or patches changed. No migration required.
- Master baseline cc765f9; task branch feature/restaurant-readonly-order-quote-r9e2.
- Native per-app existing Graphify located company resolution, native context,
  fulfillment creation and get_invoice; every conclusion was checked in source.
  Existing graph is contextual, not certification, and is not versioned.

## Validation And Rollout

Offline unittest only, bench run-tests explicitly prohibited on operational
sites by docs/test-safety.md. Block site init/connect, sockets/DNS and DB writes;
provide synthetic document/read fixtures. Exercise the real low-level native
price helper and whole-cart tax engine (not mocked numeric results). Synthetic
metadata/read selection, empty regional-hook registry and HTML rendering are
test fixtures, not arithmetic replacements. Reject active regional overrides of
the tax-engine helpers in the first supported subset. Test
inclusive/exclusive multi-item tax rounding and fee, mutations/FX absence,
permission/tenant mismatch, stale profile, ambiguous/missing/expired rates,
unsupported tax rules and item/group overrides, deterministic/change-sensitive
fingerprints, bounded inputs and exception cleanup. Native region dispatch,
real permissions/metadata and actual-site equivalence still need a separately
authorized disposable-site certification; do not claim production readiness.

## Rollback

Keep TIX adapter disabled. Revert only new module/tests/spec commits after review;
there is no inverse migration, data restoration or service reload in this task.
No commit/push until parent review. No production or operational test activation.
