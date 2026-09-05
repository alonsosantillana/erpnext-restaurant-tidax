# Validación

## Cierre de referencia

Se reconstruyeron en memoria los dos grupos del cierre `POS-CLO-ECS-2026-00008` y se
guardaron como borradores dentro de transacciones revertidas:

- `rhbspa7r94`: objetivo S/ 208.00, componentes S/ 208.00, total S/ 208.00,
  pago S/ 208.00, vuelto S/ 0.00 y castigo S/ 0.00.
- `rds3btk4jr`: objetivo S/ 132.00, componentes S/ 132.00, total S/ 132.00,
  pago S/ 132.00, vuelto S/ 0.00 y castigo S/ 0.00.

Los documentos históricos no fueron modificados.

## Pruebas

- `python3 -m py_compile`: correcto.
- Módulo `test_pos_invoice_merge`: 5 pruebas correctas.
- OpenSpec estricto: válido.
- Graphify `--code-only`: grafo regenerado; confirmó la herencia desde la clase core y
  las llamadas del conciliador a sus helpers y pruebas.

La ejecución completa de pruebas de la app no pudo iniciar por un fixture externo ya
ausente: `Parent Supplier Group: All Supplier Groups`. El módulo nuevo sí se ejecutó
de forma aislada y completa.
