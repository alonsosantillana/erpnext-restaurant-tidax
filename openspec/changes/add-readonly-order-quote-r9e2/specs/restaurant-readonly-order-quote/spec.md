## ADDED Requirements

### Requirement: Internal read-only whole-cart native quote
The service SHALL expose only an internal quote_order(proposal, context) function,
use native low-level price selection and whole-cart tax calculation, and never
persist documents, invoke POS full validation or fetch external exchange rates.

#### Scenario: Supported pickup cart
- **WHEN** the authenticated permitted user submits a valid supported Pickup cart
- **THEN** native transaction-currency lines, tax and total are returned as bounded
  decimal strings with zero delivery fee and a deterministic bounded fingerprint
- **AND** no document or database write occurs

#### Scenario: Delivery fee is an explicit native line
- **WHEN** Delivery uses a readable customer-linked address and configured fee item
- **THEN** the fee is priced and taxed exactly once in the same whole-cart engine
- **AND** product lines exclude the separate fee line

### Requirement: Fail-closed permissions and unsupported pricing
The service SHALL enforce current user, company, POS revision, service, party,
address, item and rate eligibility and reject unsupported configurations.

#### Scenario: Unsupported native price or tax context
- **WHEN** prices are absent or ambiguous, FX is required, pricing/tax rules or
  item tax overrides exist, or a permission/context check fails
- **THEN** the service rejects the quote without substituted amounts or side effects

#### Scenario: New quote revalidates inputs
- **WHEN** native configuration, eligible price or tax evidence changes
- **THEN** the service rereads that evidence and changes the fingerprint or rejects
  the quote rather than extending old approval authority

### Requirement: Offline evidence is not runtime certification
Validation SHALL exercise the actual native numeric engine under synthetic reads
and mutation/network guards without a live Frappe site.

#### Scenario: Guarded synthetic coverage
- **WHEN** local tests complete successfully
- **THEN** recorded evidence distinguishes engine tests from pending disposable-site
  permission, metadata, localization and end-to-end native equivalence certification
