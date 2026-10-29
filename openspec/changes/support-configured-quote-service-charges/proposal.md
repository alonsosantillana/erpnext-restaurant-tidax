# Configured Service Charges In Read-Only Quotes

## Problem And Goal
The internal quote rejects every template account not marked Tax, although a POS
template can intentionally combine tax and service/consumption charges. The user
confirmed configured charges apply to Pickup and Delivery, and other restaurants
may use only tax. Respect each company/POS template without fixed percentages.

## Scope And Impact
App restaurant_management, internal order_quote._taxes and its offline tests.
Accept readable active same-company leaf Tax accounts as before, plus explicitly
configured Income/Expense charge accounts with compatible non-settlement account
types and Profit and Loss report classification. Keep all other support limits.
Fingerprint eligibility fields and test the real native whole-cart engine.
The companion TIX branch updates only the aggregate label to Impuestos y cargos.

## Exclusions And Risk
Medium-high monetary validation risk; user authorized this bounded correction.
No fiscal/legal certification or recommendation to reclassify accounts. No account,
rate, tax template, Item Price, schema, hook, report, fixture, patch, migration,
credential, permission or channel setting change. No order/invoice/GL/payment
write, full POS validation or runtime rollout. Do not alter the quote API keys;
tax remains the existing total_taxes_and_charges aggregate, not IGV alone.

## Acceptance
Tax-only and tax-plus-configured-charge quotes work for both services with native
rounding/inclusion semantics. Delivery appears once, never on Pickup. Invalid
account/company/permission/rate configurations still fail closed. All offline
mutation/network guards remain untriggered. Only dedicated branches are pushed;
installed code, mainline refs and disabled gates remain untouched.
