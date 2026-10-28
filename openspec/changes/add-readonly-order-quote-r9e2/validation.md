# Local Validation And Handoff

## Scope And Git

Only `/tmp/restaurant-readonly-order-quote-r9e2`, branch
`feature/restaurant-readonly-order-quote-r9e2`, master/upstream master baseline
`cc765f95e35b7b2c8faeefa1906447c954da7522`. Seven new files; no previously
tracked file modified/deleted. No staging, commit, push, merge or rollout.
No TIX, core ERPNext, Frappe, fiscal integration or site configuration edits.

## Interface

`restaurant_management.restaurant_management.order_quote.quote_order(proposal, context)`

No HTTP whitelist. `QuoteUnavailable` is a fixed exported exception class for
known unsupported/denied contexts. TIX can map that class to unpriced handoff;
unexpected exceptions propagate and must not be cached as a priced quote.
Normalized product field is `note`, not `notes`. Result has exactly `currency`,
`lines`, `tax`, `total`, `delivery_fee`, `native_fingerprint`. Each product line
has item_code, integer qty, decimal-string rate and amount. Money has at most six
fractional digits; fingerprint is 64 lowercase hexadecimal characters. Fee is
separate from product lines but included in native grand total. Tax is the native
transaction-currency total_taxes_and_charges, not its base-currency counterpart.
Tax-inclusive line amounts already include tax.

API and human Desk revalidation use the original bound context.pos_profile, its
exact modification and current actor permissions/company/applicability. No
default-profile substitution, impersonation or role grants. Fingerprint excludes
actor identity so two eligible actors can validate identical native evidence;
TIX's receipt/consent ownership remains independently mandatory.

## Supported Subset

- Pickup or Delivery, 1..50 unique products, integer qty 1..1000, stock UOM only,
  bounded normalized notes/contact/future timezone-aware promised_at, 16KB cart.
- Company = POS = selling list currency. Foreign currency, even a locally stored
  rate, is handoff until separately certified. No external FX helper imported.
- Enabled System User, readable original profile/company/settings, enabled
  service, readable active customer and same-customer linked Delivery address.
- Positive explicit, unambiguous readable native Item Price; 100 candidate cap,
  native date/UOM/customer/packing selection helper, no automatic inserts.
- No serial/batch/variants/assets/customer-provided items, Product Bundles,
  Item or ancestor Item Group tax overrides. Exact POS item/customer group
  restrictions are conservatively enforced, not broadened by descendant lookup.
- Enabled selling Pricing Rules or any Sales Tax Rule cause conservative
  site-wide handoff, even if they may not apply to this cart. Customer/address/POS
  tax categories and internal/withholding customers are unsupported.
- Explicit nonempty same-company Sales Taxes and Charges Template with at most
  10 unique non-group Tax accounts, On Net Total nonnegative rates <=100, no
  deductions. POS posa_tax_inclusive is authoritative. Empty/no-tax templates,
  other tax types and active tax-engine regional overrides are unsupported.
- Delivery requires one configured positive-priced non-stock fee item; free,
  absent or manually quoted delivery fees require handoff. Fee cannot be a cart
  product. Pickup never appends it. Nonzero native rounding adjustment is handoff.

## Executed Checks

1. OpenSpec strict validation passed before functional edits, after tightening
   regional scope, and at the final source checkpoint:
   `openspec validate add-readonly-order-quote-r9e2 --strict --no-interactive`.
2. Final standalone run: 25 unittest methods passed, no skips, 0.202 seconds
   unittest time (0.880 seconds process wall time):

   ```bash
   PYTHONPATH=/tmp/restaurant-readonly-order-quote-r9e2 \
     /home/erpnext/frappe-bench/env/bin/python -B -m unittest \
     restaurant_management.restaurant_management.test_order_quote -v
   ```

3. Both imported service/test paths verified inside this worktree. AST parsed
   successfully with Python grammar 3.10, 3.11 and 3.12. Static call-site check
   found no save/insert/submit/commit/rollback/set_value/set_missing_values/
   validate/get_exchange_rate/new_doc/run_method calls in the new service.
4. `git diff --no-index --check /dev/null <new Python file>` reported no whitespace
   errors for both new Python files (exit 1 denotes a new-file diff).
5. Every test restores the prior werkzeug/Frappe request-local storage. Guard
   call count remained zero across site init/connect, network connect/DNS, DB
   writes/SQL, document save/insert/submit/db_set/run_method, POS validate/defaults,
   Item Price insertion and external FX lookup. No live site/database/provider
   initialized or accessed. Never used bench run-tests.

Tests execute the actual POSInvoice constructor (not mocked), Frappe rounding
methods, ERPNext get_price_list_rate_for and calculate_taxes_and_totals. Fixtures
replace only document/query reads, metadata based on core JSON with explicit
synthetic precision, child-controller resolution, empty regional-hook registry,
system settings and HTML rendering. Native arithmetic results are not mocked.
Recorded examples: exclusive cart 250 -> tax 45 / total 295; inclusive same cart
tax 38.13 / total 250; Delivery exclusive fee 10 -> total 306.8, inclusive -> 260.
The inclusive 38.13 reflects the native engine's item-wise precision, not a
replacement aggregate percentage calculation. A first expected-value assumption
of 38.14 was corrected after inspecting actual native output; no arithmetic code
was changed to force it. Earlier fixture-only runs exposed missing Global
Defaults and regional/presentation test fixtures; the final full run passes.

## Still Pending

Parent review and TIX adapter/review integration; no commit/push requested yet.
Disposable-site native equivalence, real permissions, metadata/custom fields,
localization, concurrent configuration changes and restaurant order regression
are NOT certified by synthetic tests. Adapter must remain default-off. No schema
or migration is required by this native module; no runtime changes were made.
Existing native-app Graphify was consulted and checked against source; no mixed
graph, remote provider or new/versioned graph artifact was generated. Refreshing
the source graph can be handled after parent review under its own authorization.

Suggested eventual commit: `feat: add bounded read-only native restaurant cart quote`.

## Parent Integration Review

Parent verified the exact TIX/native interface with six paired-adapter cases.
Security review found the monetary output maximum exceeded TIX's nine-integer-
digit contract. It is now 999999999.999999; an 800000 x 1000 cart with 25 percent
tax raises QuoteUnavailable instead of producing an invalid TIX quote.
The native suite now contains 26 cases. All 256 selected cross-app/local regression
methods passed together after this correction, with outer site/network guards
and each native fixture's mutation/POS/FX guards reporting zero attempts.
No disposable-site certification or runtime activation is implied.
