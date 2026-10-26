## 1. Analysis

- [x] 1.1 Revisar configuración OpenSpec, flujo POS, grafo y alcance autorizado.
- [x] 1.2 Crear rama dedicada y solicitar revisión especializada de cobros.
- [x] 1.3 Validar especificación estricta antes de implementar.

## 2. Implementation

- [x] 2.1 Resolver default habilitado del perfil sin cash hardcodeado ni fallback.
- [x] 2.2 Aplicar pagos explícitos antes de primera validación sin sustituirlos.
- [x] 2.3 Probar contratos de get_invoice y make_invoice sin DB ni escrituras reales.

## 3. Verification and handoff

- [x] 3.1 Ejecutar pruebas aisladas nuevas y regresión PedidosYa, AST y diff.
- [x] 3.2 Revisar cambio, actualizar Graphify local y registrar resultados/límites.
- [x] 3.3 Documentar reintento seguro del inbox existente y entrega Git.
- [ ] 3.4 Regresión integral con cuentas/stock/fiscal y cobro en sitio desechable.
- [ ] 3.5 Desplegar autorizado y reintentar inbox remoto existente.
