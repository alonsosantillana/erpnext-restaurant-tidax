## Context

Delivery Hero llama al plugin del POS para despachar pedidos y exige que el receptor
persista y responda en pocos segundos. Luego el plugin acepta/rechaza y notifica otros
estados usando las URLs incluidas en el payload. El middleware puede reintentar, por
lo que el token externo debe tener efecto exactamente una vez aunque la entrega sea
al-menos-una-vez.

El flujo interno ya usa `Table Order` como raiz comercial y `Restaurant Fulfillment`
como estado logistico. La integracion sera un adaptador de borde; no creara un segundo
motor de ordenes.

Graphify ubica `api.py`, `TableOrder`, `RestaurantFulfillment` y
`RestaurantCompanySettings` en la comunidad estructural de ordenes. El codigo confirma
que `create_fulfillment_order` crea cabecera/fulfillment pero no importa lineas externas,
y que el fulfillment actual exige Address para todo Delivery.

## Architecture

1. `PedidosYa Integration Settings` identifica una sucursal mediante `remote_id` y
   guarda Company, POS Profile, usuario tecnico, flujo, credenciales cifradas,
   cliente predeterminado, medios de pago, hosts de callback y mapeos de articulos.
2. `PedidosYa Order` es inbox/outbox durable. `middleware_token` es unico, el payload
   se cifra y los callbacks se guardan separadamente para auditoria controlada.
3. El endpoint Guest solo localiza la configuracion, valida el JWT y persiste. No usa
   la sesion Guest para crear documentos comerciales.
4. Una tarea cambia al usuario tecnico, descifra el payload, valida todo el pedido y
   crea orden/fulfillment/lineas en una transaccion. Solo despues envia aceptacion.
5. Los estados salientes usan un cliente HTTP con token cacheado. Cada URL pasa por
   una allowlist HTTPS para impedir SSRF.
6. Un cron recupera registros Received/Error elegibles sin duplicar trabajos.

## Model Decisions

### Authentication

- Entrada: `Authorization: Bearer <JWT>`, firma HMAC y algoritmo configurado. Se exige
  `service=middleware`; `exp` se valida cuando existe e issuer/audience solo cuando se configuran.
- Salida: `/v2/login` con `client_credentials`; el token se mantiene en cache menos
  tiempo que `expires_in`.
- No se registran JWT, contrasenas, secretos ni payloads descifrados.

### Idempotency and concurrency

- `middleware_token` es unico y el nombre del inbox se retorna como `remoteOrderId`.
- El primer receptor inserta; un duplicado devuelve el registro existente.
- El procesador bloquea la fila con `FOR UPDATE`, vuelve a comprobar el estado y solo
  crea documentos cuando aun no existe `Table Order` enlazada.
- Los callbacks salientes guardan resultado/fecha para que los reintentos sean
  observables.

### Customer and address

- Se usa el cliente predeterminado de la configuracion porque Delivery Hero declara
  varios campos del cliente como dummy/deprecados.
- Pickup no usa Address.
- Delivery propio requiere una direccion utilizable; la primera fase guarda snapshot
  del payload sin crear un Address maestro automaticamente.
- Delivery de plataforma se identifica cuando `riderPickupTime` existe. PedidosYa
  puede ocultar la direccion, por lo que se amplia fulfillment con `delivery_provider`
  y la direccion solo es obligatoria para entrega propia.

### Products and prices

- Cada producto/topping con valor comercial requiere un `remoteCode` mapeado.
- Se valida el conjunto completo antes de insertar lineas: no hay importaciones
  parciales.
- `unitPrice`, `paidPrice`, cantidad, descuentos y notas se normalizan con Decimal.
- La primera fase conserva el precio pagado por linea; la conciliacion exacta de
  descuentos patrocinados queda registrada para una fase contable posterior.

### Lifecycle

- Direct: pedido importado -> callback `order_accepted` -> platos enviados a cocina.
- Indirect: llega ya aceptado; se importa y envia a cocina sin callback de aceptacion.
- Cuando fulfillment alcanza Ready, se encola `preparation-completed` si existe URL.
- `ORDER_CANCELLED` entra por callback y cancela fulfillment cuando la transicion
  interna aun lo permite; casos facturados/despachados quedan en Error para revision.
- Las listas de estados externas son extensibles; estados desconocidos se registran
  y reconocen sin romper el endpoint.

## Affected Components

- Nuevos DocTypes `PedidosYa Integration Settings`, `PedidosYa Item Mapping` y
  `PedidosYa Order`.
- Nuevo paquete `restaurant_management.integrations.pedidosya`.
- `Restaurant Fulfillment`: proveedor logistico, direccion opcional para plataforma y
  hooks de estado preparado.
- `hooks.py`: recuperacion programada.
- `modules.txt`, traducciones y pruebas.
- Sin cambios en apps core ni en `ovenube_peru`.

## Permissions and Privacy

- Solo System Manager, Admin Resto/resto_admin administran configuracion y bitacora.
- El usuario tecnico debe estar habilitado y contar con permisos normales de orden.
- Payload cifrado y oculto; las vistas muestran identificadores, estado y error
  saneado, no direccion/telefono completos.
- El endpoint no acepta `company`, `pos_profile`, `customer` ni callback host desde el
  caller como autoridad; todo se deriva de la configuracion local.

## Risks and Mitigations

- **SSRF por callback:** HTTPS y allowlist exacta de hosts.
- **Pedido duplicado:** token unico, bloqueo y enlace uno-a-uno.
- **Precios distintos:** precio externo explicito y validacion del total; divergencia
  bloquea aceptacion.
- **Worker caido:** cron de recuperacion e inbox durable.
- **Datos personales:** cifrado, minimizacion y errores sin payload.
- **Cancelacion despues de factura:** no se automatiza nota de credito; revision manual.
- **Contrato cambiante:** parser tolera campos adicionales y callbacks ausentes.

## Migration and Rollback

Frappe crea las nuevas tablas/campos mediante `migrate`, que no se ejecutara sin
autorizacion. La integracion nace deshabilitada y no hay patch de datos. Para revertir,
se deshabilitan las configuraciones, se revierte codigo y se conservan inbox/links para
auditoria; no se borran pedidos ni facturas.

## Test Matrix

- JWT valido, expirado, firma incorrecta, header ausente.
- Remote ID inexistente/deshabilitado y usuario tecnico invalido.
- Primer dispatch, duplicado secuencial y carrera de duplicados.
- Test order sin documentos comerciales.
- Delivery plataforma, delivery propio y pickup.
- Producto/topping mapeado, desconocido, cantidad/precio invalido y total divergente.
- URL callback valida, HTTP, host no permitido y callback ausente.
- Direct/indirect, aceptacion, rechazo, prepared y cancelacion.
- Recuperacion de Received/Error y limite de intentos.
- Regresion de fulfillment manual, cocina y salon.
