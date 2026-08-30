## Context

`print_order_account` ya crea un `Restaurant Print Job` ACCOUNT durable. Las
mesas se cargan con `RestaurantObject.get_data()` y se actualizan mediante
`RestaurantObject.synchronize()`. Transferencia y pago ya notifican las mesas
afectadas despues de persistir.

El color configurado en `Restaurant Object` describe el objeto fisico y no debe
usarse como almacenamiento de un estado transitorio. El estado de pre-cuenta
pertenece a la orden activa que produjo el documento.

## Architecture

### Estado persistente

`Table Order` incorpora campos de solo lectura:

- `pre_account_status`: vacio, `Requested` u `Outdated`;
- `pre_account_requested_at`: fecha y hora de la ultima pre-cuenta encolada;
- `pre_account_requested_by`: usuario que la solicito;
- `pre_account_signature`: SHA-256 del contenido monetario vigente.

La firma contiene productos, identificadores, cantidades, precios, importes y
descuentos de linea, ademas de totales y descuento global. Excluye notas y
estados de produccion para que cocina no invalide la pre-cuenta.

### Impresion y atomicidad

`print_order_account` valida permisos de impresion y escritura, encola ACCOUNT y
marca la orden dentro de la misma solicitud. Si cualquier paso falla, la
transaccion revierte tanto el trabajo nuevo como el estado de la orden. Un
reintento exitoso reemplaza firma, usuario y fecha y devuelve `Requested`.

### Invalidacion

Durante `Table Order.validate`, una orden `Attending` con estado `Requested`
compara la firma guardada con su contenido actual. Una diferencia cambia el
estado a `Outdated`, conservando usuario y fecha como auditoria. No se permite
que una actualizacion cliente suministre directamente estos campos.

### Estado agregado de mesa

`Restaurant Object` consulta exclusivamente ordenes `Attending` de su misma
Company:

- sin ordenes activas: sin estado;
- todas `Requested`: `Requested`, usando la fecha mas reciente;
- cualquier `Outdated`: `Outdated`;
- mezcla de ordenes sin pre-cuenta y `Requested`: sin estado de proxima
  liberacion.

El agregado se incluye en `get_data()` y en las notificaciones del canal de la
mesa. No se persiste en `Restaurant Object`, evitando estados obsoletos.

### Presentacion

El cliente aplica clases CSS en cada reconciliacion:

- `pre-account-requested`: fondo ambar oscuro y badge `CUENTA`;
- `pre-account-outdated`: fondo ambar, borde rojo y badge `REIMPR.`.

La insignia incluye icono y tooltip con la fecha disponible, por lo que el color
no es el unico medio de comunicar el estado. En modo edicion se conserva la
seleccion y el estado no modifica el color configurado almacenado.

## DocTypes and APIs

- Modificado: `Table Order`.
- Lectura derivada: `Restaurant Object`.
- API modificada: `restaurant_management.api.print_order_account`.
- Sin nuevos endpoints, hooks, fixtures, reportes o dependencias.

## Permissions and Company Isolation

El usuario debe conservar permisos `print` y `write` sobre la orden. La consulta
agregada filtra por mesa, Company y estado activo. Los eventos se publican por el
canal ya autorizado de la mesa y no incluyen cliente, importes ni datos
tributarios.

## Concurrency and Realtime

La marca y su trabajo de impresion se ejecutan en una sola transaccion. Los
eventos se publican `after_commit`. Las pantallas aplican el payload autoritativo
del servidor; la recarga periodica de ambientes sigue siendo respaldo ante un
evento perdido.

## Migration

Los campos son aditivos, opcionales y con valor inicial vacio. `bench migrate`
sincroniza el esquema; no se requiere patch de datos porque las ordenes
existentes deben iniciar sin pre-cuenta activa.

## Risks and Mitigations

- **Firma inestable por redondeo:** normalizar numeros antes de serializar y
  ordenar lineas por identificador.
- **Estado marcado aunque no haya impresion:** marcar solo despues de obtener un
  trabajo ACCOUNT encolado; el estado significa solicitud aceptada por la cola,
  no confirmacion fisica de papel.
- **Eventos perdidos:** derivar siempre desde datos persistidos y conservar la
  recarga silenciosa existente.
- **Mesas con varias ordenes:** exigir que todas tengan pre-cuenta vigente antes
  de mostrar que la mesa esta proxima a liberarse.
- **Regresion visual:** usar clases limitadas a mesas, sin afectar Production
  Center ni el color guardado de configuracion.

## Test Matrix

| Area | Case | Expected |
|---|---|---|
| Queue | ACCOUNT encolado | Requested con usuario, fecha y firma |
| Queue | error de ruta/estacion | estado anterior sin cambio |
| Changes | cantidad/producto/descuento | Outdated |
| Changes | nota/estado cocina | conserva Requested |
| Reprint | ACCOUNT reencolado | Requested y firma nueva |
| Realtime | dos sesiones | ambas reciben el mismo agregado |
| Transfer | mesa origen a destino | origen limpia y destino hereda |
| Payment | orden Invoiced | mesa deja de mostrar alerta |
| Multiple | una de dos sin cuenta | no se marca proxima a liberar |
| Security | otra Company | no participa en el agregado |

## Rollback

Revertir Python, JavaScript y CSS elimina el comportamiento. Los campos aditivos
pueden permanecer sin uso para conservar auditoria; si se requiere retirarlos,
se hara en otro cambio con respaldo y patch compensatorio. No se eliminan
ordenes ni trabajos de impresion.
