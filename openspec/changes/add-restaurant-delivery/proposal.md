## Why

`Restaurant Manage` solo permite originar ordenes desde una mesa. Existen restos no funcionales de delivery basados en nombres de mesa que comienzan con `D`, campos de direccion ocultos en el formulario de pago y filtros que excluyen esas mesas de ciertas vistas. Ese comportamiento no representa de forma segura el canal, la entrega, el pago contra entrega ni su trazabilidad, y obliga a mezclar la operacion del salon con pedidos externos.

## Objective

Incorporar una primera fase operativa de delivery y recojo en tienda sobre Frappe/ERPNext v15, reutilizando productos, precios, impuestos, comandas, Production Center, clientes, pagos y facturacion existentes, sin crear mesas ficticias y sin cambiar las reglas tributarias aprobadas para salon.

## What Changes

- Agregar a `Table Order` un tipo de atencion explicito: `Dine In`, `Delivery` o `Pickup`, manteniendo `Dine In` como valor predeterminado compatible.
- Hacer obligatoria la mesa solo para salon y permitir crear ordenes delivery/recojo desde una entrada independiente de `Restaurant Manage`.
- Crear `Restaurant Fulfillment` como detalle logistico uno a uno de una orden delivery o recojo, con cliente, telefono, direccion, referencia, canal, fecha prometida, estado, forma de cobro esperada y trazabilidad.
- Guardar una instantanea de la direccion y contacto usados por el pedido, ademas de los enlaces a `Customer` y `Address`.
- Agregar un tablero operativo actualizado en tiempo real para nuevos pedidos, preparacion, pedidos listos, despacho, entrega e incidencias.
- Identificar en Production Center las comandas como salon, delivery o recojo sin inferir el tipo por el nombre de una mesa.
- Modelar la tarifa de delivery como un Item de servicio configurable agregado a la orden, para conservar calculo de impuestos, totales y traspaso a `POS Invoice`.
- Propagar direccion, contacto, canal y referencia de delivery a la informacion operativa y los campos estandar aplicables de `POS Invoice`.
- Separar estado de preparacion, estado logistico y estado de pago; `Delivered` de un plato no significara que el pedido delivery fue entregado al cliente.
- Mantener actualizaciones realtime reconciliadas contra el servidor y validar cada transicion y permiso del lado servidor.

El cambio es de **riesgo medio-alto** porque extiende el ciclo de orden, Production Center, pagos y generacion de `POS Invoice`, pero no modifica las reglas de comprobantes ni la integracion SUNAT.

## Scope

- App: `restaurant_management`.
- Pagina `Restaurant Manage`, selector de productos, administrador de ordenes, pago y Production Center.
- DocTypes `Table Order`, `Order Entry Item`, `Restaurant Settings`, `Customer`, `Address` y `POS Invoice`.
- Nuevo DocType `Restaurant Fulfillment` y registro auditable de sus transiciones.
- APIs para crear, consultar y cambiar pedidos delivery/recojo.
- Configuracion de Item de tarifa de delivery y canales manuales.
- Pruebas unitarias, de integracion y matriz funcional v15.

## Exclusions

- Integraciones con Rappi, PedidosYa, WhatsApp, tienda web u otros proveedores externos.
- Geocodificacion, mapas, optimizacion de rutas o seguimiento GPS.
- Aplicacion movil del repartidor.
- Liquidacion contable de repartidores, caja secundaria o conciliacion masiva de efectivo.
- Tarifas por poligono, distancia o proveedor externo; la primera fase acepta tarifa manual usando el Item configurado.
- Cambios en reglas SUNAT, series, payloads electronicos o apps externas.
- Migracion de supuestas mesas historicas `D...`; se parte del nuevo modelo explicito sin reinterpretar datos anteriores.

## Capabilities

### New Capabilities

- `restaurant-fulfillment`: Creacion, preparacion, despacho, recojo, entrega, pago esperado y trazabilidad de pedidos fuera del salon.

### Modified Capabilities

- `restaurant-order-lifecycle`: `Table Order` admite tipos de atencion con precondiciones diferentes y sincroniza la preparacion con fulfillment.
- `restaurant-pos-compliance`: La tarifa se factura como Item de servicio y la direccion/contacto se mapean a campos estandar aplicables de `POS Invoice`.

## Expected Impact

- Los operadores podran crear pedidos delivery sin ocupar mesas ni ambientes.
- Cocina y bar recibiran las lineas mediante el flujo existente y veran una identificacion clara del canal.
- Caja distinguira pago anticipado de pago contra entrega y no podra cerrar silenciosamente una entrega con cobro pendiente.
- El tablero delivery mostrara estado autoritativo y cambios en tiempo real en todas las pantallas abiertas.
- Las ordenes de salon existentes conservaran su comportamiento mediante el valor predeterminado `Dine In`.

Archivos y areas con impacto principal:

- `restaurant_management/restaurant_management/doctype/table_order/`.
- Nuevos DocTypes bajo `restaurant_management/restaurant_management/doctype/restaurant_fulfillment/`.
- `restaurant_management/restaurant_management/page/restaurant_manage/`.
- `restaurant_management/public/restaurant/js/` y estilos relacionados.
- `restaurant_management/restaurant_management/doctype/restaurant_object/` para Production Center.
- `restaurant_management/restaurant_management/doctype/restaurant_settings/`.
- `restaurant_management/api.py`, pruebas y traducciones.

## Acceptance Criteria

- Un usuario autorizado crea una orden `Delivery` o `Pickup` sin mesa, selecciona productos y los envia a Production Center.
- Una orden de salon sigue requiriendo mesa y funciona sin regresiones.
- Delivery exige cliente, telefono y direccion; recojo exige cliente y telefono.
- Production Center muestra canal, numero de orden y nombre del cliente sin depender de prefijos de mesa.
- Al completar todos los platos enviados, el fulfillment pasa de preparacion a listo exactamente una vez.
- Un usuario autorizado asigna, despacha y entrega un delivery mediante transiciones validas; los clientes abiertos reciben la actualizacion realtime.
- El cargo de delivery utiliza el Item configurado y coincide entre orden, pago y `POS Invoice`, respetando impuestos incluidos.
- La factura recibe el cliente, direccion y contacto aplicables sin cambiar la seleccion Boleta/Factura ni Electronica/Manual.
- Un reintento o doble clic no crea dos fulfillments, dos tarifas ni dos transiciones equivalentes.
- Las pruebas automatizadas y la matriz manual cubren salon, delivery, recojo, pago anticipado, contra entrega, cancelacion y permisos.
