# Read-only native restaurant cart quote

## Why

R9E.2 cannot bind TableOrder.get_invoice as a read-only price provider. Its
set_missing_values / POS validation path can reach Item Price insertion and
external currency-rate lookup. No such calls were executed during this audit.

## What Changes

Add the internal Python service
`restaurant_management.restaurant_management.order_quote.quote_order(proposal, context)`.
It validates the authenticated restaurant context, reads explicit native prices,
and invokes ERPNext's whole-cart tax engine on a new in-memory document only.
Unsupported contexts fail closed for manual handoff, never fabricated prices.

Scope: restaurant_management only, new module, isolated unittest suite and this
specification. Read-only inputs include User, Company, POS Profile, Restaurant
Company Settings, Customer, Address, Item/Item Group, Item Price, Price List,
Sales Taxes and Charges Template, Account, Pricing Rule and Tax Rule.

No public HTTP endpoint, TIX edits, hooks, schema, fixtures, patches, reports,
migrations, native order/invoice mutations, fiscal changes or live ERP/provider
calls. Existing order and payment behavior stays untouched. TIX owns a separate,
default-off adapter; adding this module alone does not activate pricing.

## Impact And Risk

Medium/high business-pricing risk, explicitly approved for source work only.
Initial coverage is deliberately conservative: same company/POS/list currency,
stock-UOM integer quantities, unambiguous positive explicit prices, no automatic
pricing rules, no item/group tax overrides or tax rules, bounded On Net Total
tax rows, native inclusive/exclusive calculation, configured delivery-fee item
once for Delivery and no fee for Pickup. Foreign currency, conflicting/unknown
configuration and unsupported rounding go to handoff.

## Acceptance Criteria

- No save/insert/submit, Item Price mutation, full POS validation, FX lookup or
  network access in the service path; permissions are never elevated.
- Whole-cart monetary results come from the actual native tax engine, not a
  replacement tax implementation; values are finite decimal strings of at most
  six fractional digits in transaction currency.
- Context/revision, item/party/address eligibility and prices are re-read per
  quote; deterministic bounded fingerprint changes with relevant evidence.
- Guarded offline tests exercise the service and unmodified native tax engine;
  synthetic reads are explicitly not live/native-site certification.
- Strict OpenSpec and source checks pass; live certification remains pending.
