## ADDED Requirements

### Requirement: Actionable POS currency mismatch diagnostic

When the restaurant POS currency validation rejects a price-list/profile mismatch, the system SHALL report the invoice-validation stage, POS Profile, selling Price List, and their effective currencies without exposing customer, fiscal or secret data. It SHALL continue to reject the transaction before document creation.

#### Scenario: Mismatch while building an invoice from Table Order

- **WHEN** the Table Order invoice builder encounters a price-list currency different from the POS Profile currency
- **THEN** the rejection names the order invoice-build stage and both effective configuration values, with no invoice created

#### Scenario: Mismatch while revalidating a POS Invoice

- **WHEN** the POS Invoice validation path encounters a price-list currency different from the POS Profile currency
- **THEN** the rejection names the POS Invoice validation stage and both effective configuration values

#### Scenario: Currencies match

- **WHEN** the POS Profile and selling Price List have the same currency
- **THEN** invoice currency and conversion-rate assignment remain unchanged
