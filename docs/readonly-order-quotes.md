# Internal Read-Only Order Quotes

`restaurant_management.restaurant_management.order_quote.quote_order` is an
internal Python function, not a whitelisted endpoint. It constructs an unsaved
native POSInvoice and invokes the low-level native price/tax engine for a whole
supported cart. It does not save an order, invoice or payment, run full POS
validation, admit an order or authorize a fiscal operation.

## Configuration Read Contract

The current actor must be an enabled System User with its assigned company and
the exact readable, enabled, current POS profile selected by the caller's bound
server context. Customer/address/item/price/template/account read checks remain.
The quote supports only its documented same-currency, native-pricing subset;
unsupported rules, metadata, arithmetic or permission paths fail closed.

The private Settings reader exposes only:

| Field | Purpose |
| --- | --- |
| company | Match the already authorized company |
| pos_profile | Match the exact authorized POS |
| enable_pickup / enable_delivery | Verify the selected service is enabled |
| delivery_fee_item | Price one fee line for Delivery; none for Pickup |
| name / modified | Private configuration fingerprint evidence |

This is a distinct projection-read contract, not full document authorization.
`default_customer`, reservation defaults, children, printer/fiscal fields and
other Settings values are neither selected nor returned by the quote reader.
The generic Settings form and linked Customer records can remain inaccessible.
Do not grant another Customer or set ignore_permissions to make a quote pass.

Effective runtime roles/Custom DocPerm must grant level-0 read and the read
permlevels of every selected field. Owner-only access requires the persisted
row to match the current actor through the query selector. Shares and select-only
access cannot substitute for these conditions. Native expanded User Permissions
apply to the selected Settings name and relevant Company/POS/Item Links, including
applicable_for and strict-empty behavior. Relevant fee-Link restrictions remain
in force for Pickup too. Authorization/projection results are not cached here.

Unknown Settings/wildcard permission or query-condition hooks, Permission Query
Server Scripts, Settings class overrides and unsupported metadata are rejected.
Only the native script registry is inspected; scripts are not read or executed.
Ordering is fixed to name ascending so metadata cannot sort by omitted fields.
Such extensions may require
omitted fields and need separate review; the reader does not guess their result.
The shared Settings helper and Frappe's generic permissions are unchanged.

## Amounts And Authority

Prices, configured taxes/service charges and inclusive behavior come from the
bound native company/POS/list/template, not caller-supplied rates. `tax` is the
existing native total_taxes_and_charges aggregate, not an IGV-only breakdown.
Inclusive line amounts already contain the charges; do not add them twice.
Delivery is one independently configured fee item/price; the public product lines
exclude that fee. The fingerprint changes with relevant native configuration.
No percentage, customer, company or delivery price is hardcoded by this reader.

## Safe Validation

From the native app root, using the existing bench Python environment:

```bash
"$BENCH_ROOT/env/bin/python" -B -m unittest \
  restaurant_management.restaurant_management.test_order_quote
```

These tests use synthetic storage but actual native role/applicability decisions
and price/tax arithmetic, with site initialization, writes and network blocked.
For paired TIX tests, put the reviewed native/TIX roots and TIX mcp_server/tests
on PYTHONPATH; use the matching candidate revisions, never an accidental installed
module. Read [test safety](test-safety.md) before other test commands.

Operational checks need the separately approved prepared principal/fixtures,
READ ONLY transactions, mutation/dispatch/network guards, current-source identity
and an independent after-rollback preservation comparison. Keep all channel and
admission gates off. Do not run bench run-tests on an operational site.

Code validation, applying an installed revision, live Web consent and human
approval are distinct acceptance steps. See the dedicated change
[scope-restaurant-quote-settings-read](../openspec/changes/scope-restaurant-quote-settings-read/proposal.md)
and its validation evidence for actual results and pending work.
