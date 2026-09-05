## Validation Evidence

- OpenSpec strict validation passed with the local Node 22 runtime.
- Python compilation, JavaScript syntax, JSON parsing, and git diff integrity passed.
- Ten focused Restaurant Tip unit/security tests passed.
- The v15.local migration completed and installed the settlement fields.
- A reversible integration test consolidated TIP-ECS-2026-00011 and
  TIP-ECS-2026-00012 into temporary Journal Entry JV-22039 for S/ 20.00. Its
  separate liability debits referenced collection entries JV-22027 and JV-22028,
  followed by one consolidated credit to
  10211001 - Fondo Fijo - Importaciones - ECS.
- Cancelling that temporary entry restored both tips from Settled to Collected.
  A final rollback removed JV-22039 and left both production tips unchanged.
- A reversible cashier test settled the cashier own closing POS-CLO-ECS-2026-00009
  and confirmed that Propinas Resumen omits both Journal Entry columns and values
  when the caller lacks Journal Entry read permission.
- Graphify code-only extraction indexed settle_restaurant_tips,
  restore_tips_for_cancelled_settlement, and the report selection action.
- Assets were rebuilt, cache was cleared, and the local services were restarted.
- Browser interaction smoke testing remains pending.
