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
- `openspec validate` queda pendiente porque la instalación local requiere Node 20+ y el bench usa Node 18.
