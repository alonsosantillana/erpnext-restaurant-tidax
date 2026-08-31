## Why

Las ordenes nuevas de mesa pueden persistirse inicialmente con cero comensales,
aunque la operacion normal parte de una persona. El formulario actual permite
escribir el valor, pero no ofrece una seleccion directa y consistente con la
capacidad visible de la mesa.

## Objective

Crear toda orden de mesa con un comensal por defecto y permitir seleccionar de
forma explicita una cantidad valida desde el formulario de Numero de comensales.

## Scope

- App: `restaurant_management`.
- Modulo: Restaurant Manage.
- DocType afectado: `Table Order`.
- Flujo servidor: creacion de orden desde `Restaurant Object`.
- Flujo cliente: formulario `restaurant-order-guest-count` y configuracion del
  editor en `table-order-class.js`.
- Pruebas: valor inicial de una orden de mesa y configuracion del selector.

## Exclusions

- No se cambia la capacidad configurada de las mesas.
- No se impide conservar un valor historico mayor que la capacidad actual.
- No se cambia el valor cero usado por delivery y recojo en local.
- No se modifican pagos, facturacion, impuestos, impresion ni SUNAT.

## Impact

Riesgo bajo. El cambio solo inicializa el contador de ordenes de mesa y mejora su
captura. No requiere patch de datos: las ordenes existentes conservan su valor.
La compatibilidad objetivo es Frappe/ERPNext v15.

## Acceptance Criteria

- Una orden nueva creada desde una mesa se guarda con `guest_count = 1`.
- El boton Numero de comensales abre una seleccion cuyo valor inicial refleja la
  orden actual.
- La seleccion contiene como minimo `1` y cubre la capacidad de la mesa.
- Si una orden existente supera la capacidad actual, su valor sigue disponible.
- Guardar actualiza la orden y el contador de personas de la mesa en tiempo real.
- Delivery y recojo conservan `guest_count = 0`.
