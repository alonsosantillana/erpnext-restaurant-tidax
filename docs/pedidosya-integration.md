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

### Autenticación entrante y prueba sin sesión

El JWT entrante se valida mediante `auth_hooks` antes del rechazo genérico de
Frappe a un Bearer desconocido. El hook solo reconoce las rutas exactas anteriores
(y sus equivalentes `/api/v1/method/`), con POST para dispatch y PUT/POST para
status. No habilita autenticación JWT en otras APIs ni en rutas con sufijos.
Se rechazan `cmd` que redirijan la llamada y overrides del método antes de cambiar
la identidad. No enviar `cmd` ni añadir una barra final a las URLs del webhook.

El token debe estar firmado con el secreto de la configuración habilitada, usar
HS256/HS384/HS512 según el algoritmo configurado e incluir `exp` y
`service: "middleware"`. Se validan issuer/audience cuando estén configurados;
una tolerancia de reloj de 0 se respeta. Los tokens sin vencimiento, antes
admitidos por la validación interna, ahora se rechazan. El usuario de integración
debe existir y estar habilitado; no usar los usuarios especiales `Guest` ni
`Administrator`. No se otorgan roles ni se modifica la seguridad de otras APIs.

Una prueba correcta no debe enviar cookies de administrador. Ante 401, distinguir
un rechazo global de Frappe de uno por firma, vencimiento, configuración o usuario;
no cambiar permisos ni quitar la validación JWT para hacerla pasar. El endpoint
vuelve a validar el JWT como defensa adicional. No copiar secretos ni JWT a logs,
capturas o conversaciones.

### Validación de la corrección del hook

Las pruebas aisladas se ejecutan desde la raíz de esta app, sin inicializar sitio:

```bash
PYTHONDONTWRITEBYTECODE=1 ../../env/bin/python -m unittest discover \
  -s restaurant_management/integrations/pedidosya -p 'test_*.py' -v
```

No usar `bench run-tests` sobre sitios operativos: la inicialización de ERPNext
puede eliminar Item Price. La suite usa DB simulada y ejecuta `validate_auth` y
`set_user` reales; simula OAuth, API keys, validación IP, persistencia y colas.
No sustituye una prueba HTTP/WSGI completa ni la certificación del proveedor.

La corrección no cambia esquema ni frontend: no requiere `migrate` ni `build`.
Para un despliegue posterior autorizado, actualizar código, limpiar la caché de
hooks del sitio y recargar los procesos según el modo de ejecución. Esos comandos
no forman parte de la validación aislada y requieren autorización operacional.
Repetir después la recepción con `test: true` y sin callbacks: primera entrega
202, duplicado 200 con el mismo identificador, estado final `Test` y enlaces a
orden/fulfillment vacíos. Deshabilitar la configuración de simulación al terminar.

Si PedidosYa exige literalmente `/order/{remoteId}` y `/remoteId/{remoteId}/remoteOrder/{remoteOrderId}/posOrderStatus`, publicar esos paths mediante el reverse proxy hacia los métodos anteriores. El proxy debe preservar `Authorization` y el cuerpo JSON, aceptar exclusivamente HTTPS y no reintentar respuestas 4xx.

## Operación

- `Received`: webhook persistido, pendiente de worker.
- `Processing`: se valida catálogo, precio y datos logísticos.
- `Awaiting Acceptance`: flujo directo esperando decisión humana.
- `Accepted`: pedido enviado a cocina y aceptación notificada.
- `Error`: importación fallida; el motivo visible no incluye secretos y el scheduler reintenta.
- `Review`: requiere revisión humana, por ejemplo una cancelación recibida después del despacho.

Los pedidos de prueba (`test=true`) validan autenticación, estructura y mapeo, pero no crean órdenes operativas.

### Recogidos en el tablero

En **Pedidos externos → Recojo en local**, el selector **Recogidos del día** muestra
los pedidos recogidos y pagados en la fecha elegida. Inicialmente selecciona hoy,
según la zona horaria del sitio. La fecha se obtiene del historial de la transición
a Recogido; editar o pagar después no cambia el día de recogida.

Los pendientes de fechas anteriores siguen visibles, incluidos recogidos sin pago.
La fecha solo limita los recogidos ya pagados. La columna **Recogido** cuenta sus
tarjetas visibles; los contadores superiores siguen indicando únicamente pendientes.
Por ejemplo, un recogido pagado puede aparecer en su columna y el contador de
pendientes mantenerse en cero. El selector se conserva al actualizar en tiempo real.

La vista mantiene los límites de 200 pendientes y hasta 200 recogidos pagados del
día por consulta, restringidos a la compañía/perfil POS activos y permisos de lectura.
Para auditoría completa usar la lista de Restaurant Fulfillment. Los históricos sin
transición auditada no reciben una fecha de recogida inventada. Mostrar una tarjeta
no modifica su estado, pago, comprobante ni datos del pedido. Delivery no cambia.

### Medio de pago al calcular e importar

El perfil POS debe tener un único medio de pago predeterminado habilitado y una
cuenta configurada para la compañía. El cálculo usa ese medio en una factura
temporal, sin guardar comprobantes, cobrar ni generar asientos. No depende de un
medio global llamado `cash` ni habilita métodos automáticamente. Si falta un
predeterminado válido, el error identifica el perfil que debe revisarse.

Al cobrar, se conservan los medios e importes seleccionados por el cajero, también
en pagos mixtos. Las validaciones estándar de ERPNext continúan aplicándose a los
medios usados y sus cuentas. El estado logístico `Prepaid` de PedidosYa no equivale
a una contabilización automática del cobro.

Si un inbox falló con `Mode of Payment cash is disabled`, después de publicar y
desplegar la corrección usar **Retry Processing** en el registro existente, siempre
que no tenga orden enlazada. No enviar un token nuevo: generaría otra recepción.
En flujo Direct con autoaceptación apagada, esperar `Awaiting Acceptance`, una sola
orden y fulfillment, sin aceptar, cobrar ni emitir durante esta comprobación.
El scheduler también puede reintentar el registro; revisar sus enlaces antes de
repetir acciones. Esta corrección Python no requiere `migrate` ni `build`.

## Activación segura

1. Desplegar código y ejecutar la migración en una ventana controlada.
2. Configurar primero el ambiente **Staging** y cargar credenciales por canal seguro.
3. Probar duplicados, código no mapeado, total diferente, delivery PedidosYa sin dirección, delivery propio con dirección, pickup, rechazo, cancelación y callback de listo.
4. Revisar workers y scheduler; no activar si las colas están detenidas.
5. Completar certificación y recién entonces cambiar a Production y habilitar el registro.

Referencias oficiales: [Delivery Hero POS integration](https://developers.deliveryhero.com/documentation/pos.html), [POS Plugin API](https://integration-middleware.stg.restaurant-partners.com/apidocs/pos-plugin-api) y [POS Middleware API](https://integration-middleware.stg.restaurant-partners.com/apidocs/pos-middleware-api).
