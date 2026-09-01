# Validación

## Automatizada

- `bench --site v15.local migrate`: completado; el parche de configuración se
  ejecutó correctamente.
- 5 pruebas de contabilidad de gastos: correctas.
- 6 pruebas del controlador `Resto Gastos`: correctas.
- 4 pruebas de conciliación de gastos en cierre POS: correctas.
- 11 pruebas de series multiempresa: correctas.

Total dirigido: 26 pruebas correctas.

## Prueba transaccional reversible

Con la apertura activa `POS-OPE-ADA-2026-00003` se creó y envió temporalmente
un gasto de S/ 1.23. El resultado fue:

- `Journal Entry` enviado con débito S/ 1.23 y crédito S/ 1.23.
- Cuenta de pago tomada automáticamente del método de pago de la apertura.
- La cancelación del gasto canceló también el asiento.
- La transacción completa se revirtió con un savepoint; no quedaron documentos
  ni configuración de prueba.

## Configuración detectada

- ERPCLOUD tiene como respaldo `00000000000000 - Gastos Varios - ECS`.
- ADDERA no recibió respaldo porque su cuenta `Gastos Varios` está deshabilitada.
  Debe seleccionarse una cuenta habilitada en `Restaurant Company Settings` o
  configurarse una cuenta por producto en `Item Default` antes de enviar gastos.

## OpenSpec CLI

`openspec validate account-resto-gastos-on-submit --strict` no pudo ejecutarse:
la instalación actual de OpenSpec usa expresiones regulares `/v`, que requieren
Node 20 o superior, mientras el bench utiliza Node 18.20.8.
