## Why

Los pedidos de PedidosYa se reciben fuera de Restaurant Management y deben volver a
digitarse, por lo que pueden divergir productos, precios, observaciones, estados y
pagos. La app ya dispone de `Table Order`, cocina y `Restaurant Fulfillment`, pero no
tiene un adaptador autenticado ni una bitacora idempotente para Delivery Hero POS
Middleware.

## Objective

Incorporar una primera integracion oficial y desactivada por defecto con PedidosYa
Restaurant POS, capaz de recibir y persistir pedidos de forma segura, transformarlos
asincronamente al flujo existente y devolver estados mediante los callback URLs
autorizados por el proveedor.

## Scope

- App `restaurant_management`, compatible con Frappe/ERPNext v15.
- Configuracion por Company, POS Profile y `remote_id` de sucursal.
- Credenciales cifradas, validacion JWT entrante y autenticacion Bearer saliente.
- Registro durable e idempotente de cada token externo y payload cifrado.
- Mapeo explicito `remoteCode -> Item` y soporte inicial de toppings como lineas o
  notas segun su mapeo.
- Importacion asincrona a `Table Order` y `Restaurant Fulfillment` sin mesa.
- Flujo Delivery de plataforma, Delivery propio y Pickup.
- Aceptacion/rechazo, cancelacion recibida y notificacion de pedido preparado.
- Recuperacion programada de eventos pendientes o fallidos.
- Pruebas unitarias de autenticacion, idempotencia, URL saliente, mapeo y estados.

El cambio es de **riesgo medio-alto** por exponer una entrada HTTPS externa y tocar
precios/estados de orden. No se activa en ninguna compania ni usa credenciales reales
durante la implementacion.

## Exclusions

- Activar una cuenta real, ejecutar `migrate`, reiniciar servicios o modificar datos.
- Sincronizacion completa Catalog Import API en esta fase.
- Autoemision SUNAT/Nubefact, notas de credito, liquidacion semanal o contabilizacion
  de comisiones de PedidosYa.
- Modificacion de productos de un pedido ya aceptado.
- Aplicacion de repartidor, geocodificacion o tracking GPS.
- Prometer campos no incluidos por PedidosYa; propiedades desconocidas se ignoran.

## Expected Impact

- Los pedidos externos confirmados entran una sola vez y reutilizan cocina y tablero.
- Las ordenes de prueba quedan en la bitacora y nunca llegan a produccion.
- Los precios del payload se conservan sin depender del precio vigente del catalogo.
- Fallos de configuracion o mapeo quedan visibles y reintentables, sin aceptar
  silenciosamente un pedido incompleto.
- Salon, delivery manual, pagos y facturacion existentes no cambian si la integracion
  permanece deshabilitada.

## Acceptance Criteria

- Un webhook con JWT valido y `remote_id` habilitado persiste una sola orden externa
  y devuelve el mismo `remoteOrderId` ante reintentos.
- Un JWT invalido, sucursal desconocida o integracion deshabilitada no crea documentos.
- El endpoint reconoce rapido el pedido y difiere la transformacion a una cola.
- Un pedido normal con todos sus `remoteCode` mapeados crea una `Table Order` externa,
  un fulfillment y sus lineas con cantidades, precios y observaciones recibidas.
- Un pedido `test=true` nunca crea orden de cocina.
- Un codigo sin mapeo deja el registro en Error y permite rechazar con motivo, sin
  generar una orden parcial.
- Solo se invocan callback URLs HTTPS cuyo host esta autorizado en configuracion.
- La cancelacion entrante es idempotente y queda auditada.
- Las pruebas existentes de delivery manual y salon permanecen verdes.
