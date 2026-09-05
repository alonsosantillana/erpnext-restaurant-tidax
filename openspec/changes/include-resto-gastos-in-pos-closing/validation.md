# Validación

| Caso | Resultado esperado |
|---|---|
| Apertura 100 + ventas 500 - gastos 80 | Esperado 520 |
| Contado 515 con esperado 520 | Diferencia -5 |
| Dos guardados consecutivos | Esperado permanece 520 |
| Gasto de otra apertura | No se descuenta |
| Gasto en borrador | Cierre bloqueado |
| Cancelar gasto después del cierre | Cancelación bloqueada |
| Reporte con dos aperturas el mismo día | Cada gasto se asocia por apertura |

## Resultado automatizado

- 21 pruebas unitarias aprobadas.
- Migración de `v15.local` completada.
- Metadatos verificados en base de datos.
- Resumen real verificado: S/ 12.00 en Efectivo para `POS-OPE-ADA-2026-00002`.
- Validacion estricta de OpenSpec aprobada usando Node 22 local.
\n\n## Correccion de resumen obsoleto - 2026-09-05\n\n- Cuatro pruebas focalizadas de conciliacion y gastos aprobadas.\n- POS-CLO-ECS-2026-00008 verificado con total S\/ 340.00, neto S\/ 275.29, cantidad 13, ventas BCP S\/ 232.00 y efectivo S\/ 108.00.\n- El render directo del servidor devuelve los datos correctos de 00008; S\/ 533.20, S\/ 431.72 y cantidad 22 pertenecen exactamente a 00007.\n- El resumen ahora se reconstruye desde el documento actual y muestra ventas brutas por metodo antes de gastos.\n- Sintaxis JavaScript aprobada y grafo Graphify regenerado.\n