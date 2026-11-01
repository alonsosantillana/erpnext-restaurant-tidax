# Design

## Sources And Baseline
Remote native primary is master cc765f9; the required installed quote prerequisite
8e0ac16 is not merged there. The new task worktree starts from master and
fast-forwards that prerequisite, leaving installed source unchanged. Existing
Graphify _context/get_restaurant_settings nodes were verified against code and
Frappe permissions.py, effective Meta permissions, get_permitted_fieldnames and
get_user_permissions/get_allowed_docs_for_doctype. No per-app AGENTS was present.
The bench specialized-review guide explicitly requires architecture/security
review; the independent reviewer confirmed all-Link filtering and warned against
role-only checks, share rescue and passing partial documents as full documents.

## Private Projection Authorization
Introduce one private _quote_settings(company, pos_profile), called only after the
existing active System User, current company, readable Company and exact readable
POS checks. Recheck actor/company binding inside the reader. Do not accept a
caller actor, Settings name, field list or permission flag.

The fixed domain projection is company, pos_profile, enable_pickup,
enable_delivery, delivery_fee_item. Only name/modified are extra system columns.
No default/reservation customer, child table, printer/fiscal or other Settings
column is selected. Return a plain read DTO, not a forged partial Document.
Generic Settings/full-form permissions remain unchanged and may still deny.

Read effective runtime Meta/Custom DocPerm and current roles for level-0 read and
every allowlisted field's permlevel. Validate expected Link/Check field types,
Link targets and nonvirtual metadata. Reject Single/Table/virtual Settings.
Use the real native role permission evaluator plus explicit read permlevel and
if_owner qualification. If any necessary read is owner-only, include owner=current
actor in the SQL selector, rather than reading unauthorized fields first. Shares
and select-only access cannot rescue a denied projection.

Select at most two company rows, with fixed fields and optional owner filter;
set fixed ordering by name ascending, never metadata-selected sort fields;
require exactly one and require its stored profile to equal the previously
authorized POS. A missing/blank/mismatched/ambiguous binding is not a fallback.
Apply native expanded User Permissions/applicable_for separately to Settings name
and selected Company/POS/Item Links. Preserve strict-empty behavior for the fee
Link even on Pickup. Unrelated customer Links are not part of this contract.
Do not cache the projection or authorization between actors/requests.

Fail closed whenever Settings or wildcard has_permission/query-condition hooks,
Permission Query Server Scripts or a Settings class override are registered.
Read only the native server-script registry, never script bodies or execution:
arbitrary policies may need omitted
fields and cannot be safely inferred from a projection. No hook true or shared
document can bypass role, owner, field or User Permission checks. No changes to
the generic Frappe permission engine or shared get_restaurant_settings helper.

## Files And Data
Modify order_quote.py/test_order_quote.py only for execution. Add a focused guide
docs/readonly-order-quotes.md and documentation index, and link from README.
No hooks, DocTypes, APIs, JS, fixtures, patches, database or permission records
change. No new dependencies or migrations. Existing fingerprint fields still
include Settings name/modified/relevant values; forbidden values never enter it.

## Tests And Acceptance
Guarded offline native tests exercise the real whole-cart engine with synthetic
metadata/storage. Keep native role and applicable User Permission decisions real;
mock only stored roles, permission records and document/query reads. Add cases for
irrelevant customer denial with successful projection, exact selected columns,
role/select/owner/field-level denials, custom effective permission replacement,
record/Link scope, strict empties, wrong/ambiguous/missing bindings, unknown hooks/
overrides/Server Scripts, fixed native query ordering despite hostile sort metadata,
actor switching/revocation, and no forbidden evidence/output. Rerun
paired TIX/native adapter tests without changing TIX functional source.

The previous quote-only site authorization remains usable for a candidate-source
READ ONLY trial with the private prepared scenario and mutation/network guards.
Record candidate import identity and keep installed refs/gates/data unchanged.
Success is candidate native-function evidence, not installed/live Web or fiscal
certification. If unrelated metadata/calculation fails, report it separately; do
not silently broaden code or source support.

## Rollback
Before installation, discard/revert only dedicated task commits after review;
installed source and data require no reversal. A later installed update requires
separate authorization and retains 8e0ac16 as source rollback. No inverse schema
migration, permission grant rollback or data restoration is needed. Never run a
reset, restoration, service restart or gate change as an implicit test repair.
