## Why

TableOrder.get_invoice fuerza un pago temporal llamado cash antes de validar una
Factura POS. Un cash deshabilitado impide calcular/importar pedidos PedidosYa y
también bloquea el cobro antes de aplicar los medios elegidos por el cajero.

## What Changes

- Para cálculos sin cobro explícito, usar únicamente el medio predeterminado
  habilitado del perfil POS de la empresa de la orden.
- Mostrar error de configuración si falta un único predeterminado válido, sin
  seleccionar arbitrariamente otro medio ni habilitar cash.
- Pasar los pagos reales de make_invoice a get_invoice antes de su primera
  validación y conservar sus medios e importes, incluidos pagos mixtos.
- Añadir pruebas aisladas y guía para reintentar el inbox fallido existente.

## Impact

Solo restaurant_management: Table Order, sus pruebas y documentación. Riesgo alto
por método compartido de cálculo/cobro; autorizado por el usuario tras explicación.
Sin cambios en core, hooks, APIs públicas, DocTypes, permisos, fixtures, precios,
impuestos, contabilidad, configuración ni datos. Sin migrate, restart o despliegue.

## Acceptance Criteria

Un perfil con default habilitado calcula sin cash. Default ausente, múltiple o
deshabilitado produce error orientado al perfil. Pagos explícitos no se sustituyen
por defaults y un mapping vacío no se convierte en cobro implícito. La factura de
cálculo no se guarda ni presenta; continúan las validaciones nativas y de moneda.
