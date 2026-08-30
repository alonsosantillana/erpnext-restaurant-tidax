## Why

Cuando se solicita e imprime una pre-cuenta, el mapa de mesas conserva el mismo
aspecto de una mesa ocupada. Caja y salon no pueden distinguir que esa mesa esta
en etapa de cobro y proxima a liberarse, especialmente cuando trabajan desde
pantallas diferentes.

## Objective

Representar de forma persistente, auditable y en tiempo real la etapa de
pre-cuenta de una orden de mesa, incluyendo una alerta cuando el contenido
monetario cambia despues de imprimirla.

## What Changes

- Registrar en `Table Order` la solicitud vigente de pre-cuenta, usuario, fecha y
  una firma del contenido monetario impreso.
- Marcar la pre-cuenta solamente cuando el trabajo ACCOUNT queda encolado.
- Invalidar la pre-cuenta cuando cambien productos, cantidades, precios o
  descuentos, sin invalidarla por notas o estados de cocina.
- Derivar el estado visual de cada mesa desde sus ordenes activas y publicarlo
  mediante los eventos realtime existentes.
- Mostrar la mesa en ambar con una insignia CUENTA; una pre-cuenta desactualizada
  conserva la alerta con borde rojo e indicacion de reimpresion.
- Conservar el estado al transferir la orden y retirarlo automaticamente del mapa
  cuando la orden queda facturada.

## Capabilities

### New Capabilities

- `pre-account-table-state`: Estado persistente y visual de pre-cuenta para mesas,
  con invalidacion monetaria, auditoria y sincronizacion multiusuario.

### Modified Capabilities

No existen especificaciones base en `openspec/specs/` que deban modificarse.

## Scope

- App: `restaurant_management`.
- Modulos: impresion de pre-cuenta, ordenes de mesa y mapa de ambientes.
- DocTypes: `Table Order` y lectura derivada desde `Restaurant Object`.
- APIs: `restaurant_management.api.print_order_account`.
- Frontend: `restaurant-object-class.js` y `restaurant-object.css`.
- Tiempo real: canales existentes de `Table Order` y `Restaurant Object`.

## Exclusions

- No se modifica el formato de impresion de la pre-cuenta.
- No se cambia la cola durable ni el transporte de `silent_print`/HWB.
- No se modifica facturacion electronica, pagos, impuestos ni reglas SUNAT.
- No se agrega un workflow manual separado para liberar mesas.
- No se implementan alarmas sonoras ni notificaciones fuera del mapa de mesas.

## Impact

El cambio es de riesgo medio: agrega metadatos y estado operacional, pero no
altera importes, comprobantes ni inventario. Requiere sincronizar el DocType en
Frappe v15 y reconstruir assets. No agrega dependencias, hooks, fixtures ni
reportes.

Archivos previstos:

- `restaurant_management/restaurant_management/doctype/table_order/table_order.json`
- `restaurant_management/restaurant_management/doctype/table_order/table_order.py`
- `restaurant_management/restaurant_management/doctype/restaurant_object/restaurant_object.py`
- `restaurant_management/api.py`
- `restaurant_management/public/restaurant/js/restaurant-object-class.js`
- `restaurant_management/public/restaurant/css/restaurant-object.css`
- pruebas de `Table Order` y `Restaurant Object`.

## Acceptance Criteria

- Al encolar correctamente Cuenta, la orden guarda usuario, fecha, estado y firma.
- La mesa cambia en tiempo real a ambar con una indicacion textual CUENTA en todas
  las sesiones de la misma empresa.
- Un cambio monetario posterior marca la pre-cuenta como desactualizada y solicita
  reimpresion; notas y cambios de cocina no lo hacen.
- Reimprimir Cuenta restaura el estado vigente y actualiza la auditoria.
- Transferir conserva el estado en la mesa destino y limpia la mesa origen.
- Facturar elimina la alerta al dejar de existir una orden activa en esa mesa.
- Una mesa con varias ordenes solo aparece proxima a liberarse cuando todas sus
  ordenes activas tienen una pre-cuenta vigente.
- Fallar antes de encolar la impresion no marca la orden ni la mesa.
