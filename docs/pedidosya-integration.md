# Integración POS con PedidosYa

Esta integración recibe pedidos de PedidosYa/Delivery Hero, los registra de forma idempotente y los convierte de manera asíncrona en una **Orden de restaurante** y un **Restaurant Fulfillment**. El webhook confirma recepción antes de ejecutar la lógica pesada, de modo que los reintentos del middleware no creen pedidos duplicados.

## Alcance implementado

- JWT entrante con secreto cifrado y algoritmo permitido explícitamente.
- Token de middleware único y huella SHA-256 del payload para idempotencia.
- Payload almacenado en un campo `Password`, no en logs ni campos públicos.
- Mapeo `remoteCode` de productos y toppings a artículos ERPNext.
- Los toppings gratuitos quedan detallados en las notas del plato; los toppings cobrables se importan como líneas para conservar precio y consumo.
- Delivery con repartidor PedidosYa, delivery propio del restaurante y recojo en local.
- Flujo indirecto con aceptación automática y flujo directo con botones **Accept Order** / **Reject Order**.
- Callbacks de aceptación, rechazo y pedido listo con token OAuth de corta duración.
- Webhook de cancelación y recojo por el rider.
- Recuperación cada cinco minutos para importaciones fallidas, hasta diez intentos.

No se crea automáticamente una factura, dirección, cliente ni artículo maestro. Tampoco se acepta una diferencia entre el total externo y el total calculado por el POS por encima de la tolerancia configurada.

## Configuración

Después de instalar los DocTypes mediante el procedimiento normal de despliegue, crear un registro **PedidosYa Integration Settings** por `remoteId`:

1. Seleccionar compañía, perfil POS y un usuario de integración dedicado con permisos para crear `Table Order`, `Order Entry Item` y `Restaurant Fulfillment`.
2. Seleccionar el cliente genérico que representará las ventas PedidosYa.
3. Registrar el `remoteId`, flujo Direct/Indirect, URL base, usuario, contraseña, secreto JWT y, si aplica, issuer/audience.
4. Ingresar un hostname exacto por línea en **Allowed Callback Hosts**. La URL base ya queda autorizada automáticamente.
5. Mapear cada `remoteCode` del catálogo, incluidos toppings cobrables, a un artículo de venta habilitado.
6. Si PedidosYa cobra delivery, configurar también el artículo de tarifa de delivery en Restaurant Company Settings.
7. Mantener **Enabled** apagado hasta completar pruebas de staging y certificación con PedidosYa.

Los endpoints Frappe son:

- `POST /api/method/restaurant_management.integrations.pedidosya.api.dispatch_order?remote_id=<remoteId>`
- `PUT /api/method/restaurant_management.integrations.pedidosya.api.update_order_status?remote_id=<remoteId>&remote_order_id=<remoteOrderId>`

Si PedidosYa exige literalmente `/order/{remoteId}` y `/remoteId/{remoteId}/remoteOrder/{remoteOrderId}/posOrderStatus`, publicar esos paths mediante el reverse proxy hacia los métodos anteriores. El proxy debe preservar `Authorization` y el cuerpo JSON, aceptar exclusivamente HTTPS y no reintentar respuestas 4xx.

## Operación

- `Received`: webhook persistido, pendiente de worker.
- `Processing`: se valida catálogo, precio y datos logísticos.
- `Awaiting Acceptance`: flujo directo esperando decisión humana.
- `Accepted`: pedido enviado a cocina y aceptación notificada.
- `Error`: importación fallida; el motivo visible no incluye secretos y el scheduler reintenta.
- `Review`: requiere revisión humana, por ejemplo una cancelación recibida después del despacho.

Los pedidos de prueba (`test=true`) validan autenticación, estructura y mapeo, pero no crean órdenes operativas.

## Activación segura

1. Desplegar código y ejecutar la migración en una ventana controlada.
2. Configurar primero el ambiente **Staging** y cargar credenciales por canal seguro.
3. Probar duplicados, código no mapeado, total diferente, delivery PedidosYa sin dirección, delivery propio con dirección, pickup, rechazo, cancelación y callback de listo.
4. Revisar workers y scheduler; no activar si las colas están detenidas.
5. Completar certificación y recién entonces cambiar a Production y habilitar el registro.

Referencias oficiales: [Delivery Hero POS integration](https://developers.deliveryhero.com/documentation/pos.html), [POS Plugin API](https://integration-middleware.stg.restaurant-partners.com/apidocs/pos-plugin-api) y [POS Middleware API](https://integration-middleware.stg.restaurant-partners.com/apidocs/pos-middleware-api).
