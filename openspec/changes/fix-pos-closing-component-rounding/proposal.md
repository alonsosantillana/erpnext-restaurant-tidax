## Why

Las Facturas POS con muchas líneas pueden acumular varios céntimos de diferencia al
redondear cada importe neto y cada impuesto. El cierre actualmente solo concilia un
céntimo y bloquea comprobantes válidos como `BV-BRE2-000022`, cuya diferencia es
S/ 0.03 sobre once líneas y dos impuestos.

## Objective

Conciliar únicamente diferencias que puedan explicarse por el máximo error agregado
de redondeo de los componentes, sin modificar la Factura POS original ni ocultar
desbalances contables reales.

## What Changes

- Calcular una tolerancia por comprobante a partir de sus líneas e impuestos no nulos.
- Mantener una tolerancia mínima de una unidad de precisión monetaria.
- Aplicar por separado el residual del documento y el residual en moneda base.
- Conservar la asignación del residual dentro de la misma Factura POS.
- Mantener el bloqueo cuando el residual supera el límite matemático.
- Cubrir ventas, devoluciones, moneda base y diferencias inválidas con pruebas.

## Exclusions

- Modificar o cancelar Facturas POS emitidas.
- Cambiar importes de impuestos de origen.
- Crear asientos de redondeo o utilizar cuentas de gasto.
- Aceptar diferencias sin un límite derivado de los componentes.

## Acceptance Criteria

- `BV-BRE2-000022` puede consolidarse con diferencia final S/ 0.00.
- El total e impuestos del comprobante permanecen sin cambios.
- Una diferencia superior al máximo de redondeo continúa bloqueando el cierre.
- Las devoluciones conservan el signo y la moneda base se concilia independientemente.
