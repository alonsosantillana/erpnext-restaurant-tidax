## Validation

Date: 2026-08-27
Site: v15.local
Companies: ADDERA PERU SAC, ERPCLOUD SAC

### Automated checks

- JavaScript syntax: pay-form-class.js passed node --check.
- Python syntax: tip controller, Table Order, settings, and reports passed py_compile.
- DocType JSON: Restaurant Tip and Restaurant Company Settings passed jq parsing.
- Patch quality: git diff --check passed.
- Migration: bench --site v15.local migrate completed successfully.
- Assets and translations: bench build --app restaurant_management completed successfully.
- Reports: Propinas Resumen and Resumen Cierre de Caja executed for ADDERA without SQL errors.
- Hook: POS Invoice on_cancel resolves to cancel_tip_for_invoice.

### Transactional accounting test

A reversible database test was executed for each company with a S/ 1.11 tip and
Efectivo as the collection method.

- ADDERA created a submitted and balanced Journal Entry: debit S/ 1.11, credit S/ 1.11.
- ERPCLOUD created a submitted and balanced Journal Entry: debit S/ 1.11, credit S/ 1.11.
- Both tests generated company-specific Restaurant Tip names.
- The transaction was rolled back and no Restaurant Tip or test Journal Entry remained.

### Site configuration

- ADDERA PERU SAC: enabled, liability account 4199 - Propinas por pagar - ADA.
- ERPCLOUD SAC: enabled, liability account 4199 - Propinas por pagar - ECS.
- Efectivo resolves to a company-specific Asset account in both companies.

### Real cashier validation

Both companies completed a real browser payment with an electronic voucher and
an independently accounted tip:

- ERPCLOUD SAC: voucher BV-BRE2-000002, consumption S/ 60.00, tip S/ 6.00 in
  cash, Restaurant Tip TIP-ECS-2026-00001, and submitted Journal Entry JV-22006.
  The entry debits S/ 6.00 to the ERPCLOUD collection account and credits S/ 6.00
  to 4199 - Propinas por pagar - ECS.
- ADDERA PERU SAC: voucher FV-FRE1-000003, consumption S/ 89.25, tip S/ 10.00 in
  cash, Restaurant Tip TIP-ADA-2026-00001, and submitted Journal Entry JV-22007.
  The entry debits S/ 10.00 to the ADDERA collection account and credits S/ 10.00
  to 4199 - Propinas por pagar - ADA.

The Restaurant Tip records are in Collected status and both Journal Entries are
submitted and balanced. This closes the real cashier multi-company validation.

### OpenSpec CLI

openspec validate add-restaurant-tips --strict could not run because the installed
CLI uses JavaScript syntax unsupported by Node.js 18.20.8 on this server. The change
structure and requirements were reviewed manually.
