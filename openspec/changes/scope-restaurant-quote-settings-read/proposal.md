# Scope Restaurant Quote Settings Reads

## Problem And Goal
The prepared channel principal is correctly restricted to its own customer, but
full Settings document authorization also checks the unrelated default_customer
Link. Both real full quotes stop before calculation. The user approved a narrow
configuration-field read without granting other customers or changing settings.

## Scope
Native restaurant_management internal order_quote._context and tests. Replace
the full-document Settings read with a private, fixed five-field projection for
company, pos_profile, enable_pickup, enable_delivery and delivery_fee_item, plus
name/modified fingerprint metadata. Retain effective role/field permissions,
owner qualification, record and relevant Link User Permissions, actor/company/
readable POS binding and all other quote authorization.

## Exclusions And Risk
High security sensitivity: this defines a distinct internal projection-read
contract, not generic full-document access. Unknown custom authorization hooks
or Settings class overrides fail closed. No whitelist endpoint, permission flag,
impersonation, global permission grant, settings/default-customer/price/tax/master
change, fixture, schema, migration, service action or order/invoice/payment write.
No deployment, principal merge or channel activation is included in code approval.

## Acceptance
The projection never queries forbidden Settings data/children and never returns
them in evidence/output. A customer restriction irrelevant to selected fields no
longer blocks calculation; Customer/Address document reads remain unchanged.
Every relevant denial still fails, including select-only, owner-only nonowner,
field permlevel, exact Settings name, company/POS/Item restriction, ambiguous or
foreign binding and custom authorization extension. Read-only candidate trials
may reuse the previously approved synthetic site scenario without installing code.
Specialist review, guarded native/paired regression tests, source inspection and
documented rollback precede publication. No unsupported result is called passing.
