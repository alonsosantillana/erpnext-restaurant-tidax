## Context

El frontend y el modelo actuales estan construidos alrededor de `Restaurant Object` de tipo Table: la mesa crea `Table Order`, recibe sus eventos realtime y aporta la descripcion usada por cocina. No obstante, `Table Order.table` no es requerido en metadata y ya contiene enlaces a `Customer` y `Address`. El pago incluye campos de delivery ocultos, pero no los envia a `make_invoice`. Tambien quedan consultas y filtros que clasifican delivery con `table_description LIKE 'D%'`.

La implementacion debe extender el flujo estable sin duplicar el motor de productos, impuestos, descuentos, comandas ni factura. Debe preservar Frappe/ERPNext v15 y no modificar apps core.

## Goals / Non-Goals

**Goals:**

- Crear delivery y recojo sin objetos Restaurant Table artificiales.
- Reutilizar `Table Order` y `Order Entry Item` como fuentes comerciales y de preparacion.
- Separar preparacion, logistica y cobro para evitar estados ambiguos.
- Mantener totales e impuestos autoritativos mediante el calculo existente de ERPNext.
- Proporcionar una interfaz simple, visible y realtime para operacion manual.
- Preservar compatibilidad con ordenes de salon ya existentes.

**Non-Goals:**

- Resolver integraciones de marketplaces, mapas o rutas en esta fase.
- Crear una aplicacion especializada para repartidores.
- Reescribir `Restaurant Manage` con otro framework.
- Convertir el estado `Delivering` de `Order Entry Item` en un estado logistico.
- Cambiar el momento legal de emision ni las reglas tributarias sin aprobacion adicional.

## Decisions

### 1. `Table Order` permanece como raiz comercial

Se agregara `service_type` con valores internos estables `Dine In`, `Delivery` y `Pickup`. El nombre tecnico del DocType se conserva para no duplicar items, impuestos, descuentos, division, pago ni vinculos a `POS Invoice`. En la interfaz se mostrara como Orden de restaurante cuando el contexto no sea una mesa.

`Dine In` sera el valor predeterminado y un patch idempotente lo aplicara a registros sin valor. Las reglas seran:

- `Dine In`: requiere `table` y deriva `room`.
- `Delivery`: no admite mesa y requiere un `Restaurant Fulfillment` de tipo Delivery.
- `Pickup`: no admite mesa y requiere un fulfillment de tipo Pickup.

Las funciones que hoy desreferencian siempre `_table` se adaptaran mediante una fuente de contexto: mesa real para salon y contexto de fulfillment para delivery/recojo. Division y transferencia de mesa quedaran disponibles solo para salon en esta fase.

Alternativas descartadas:

- **Mesas D1, D2...:** mezcla ocupacion con logistica, limita concurrencia y depende de nombres.
- **Nuevo motor Delivery Order completo:** duplicaria calculos y aumentaria el riesgo de divergencia tributaria.

### 2. Detalle logistico uno a uno

`Restaurant Fulfillment` tendra nombre propio y un enlace unico a `Table Order`. Guardara:

- `fulfillment_type`: Delivery o Pickup.
- cliente y direccion enlazados;
- nombre, telefono y direccion renderizada como instantaneas;
- referencia e instrucciones;
- canal manual y `external_order_id` opcional;
- fecha/hora prometida;
- usuario o repartidor asignado opcional;
- metodo de pago esperado y estado de cobro;
- estado logistico y marcas de tiempo/usuarios de las transiciones.

El enlace conserva datos maestros; la instantanea conserva el hecho historico. El servidor impedira mas de un fulfillment activo para la misma orden.

### 3. Estados separados

`Order Entry Item.status` seguira describiendo el plato en produccion. `Table Order.status` seguira describiendo si la orden esta abierta o facturada. `Restaurant Fulfillment.status` describira la atencion externa:

| Tipo | Estados validos |
|---|---|
| Delivery | New, Preparing, Ready, Assigned, Out for Delivery, Delivered, Delivery Failed, Cancelled |
| Pickup | New, Preparing, Ready, Picked Up, Cancelled |

`New -> Preparing` ocurre al enviar por primera vez platos a produccion. `Preparing -> Ready` ocurre cuando todas las lineas positivas que fueron enviadas alcanzan el estado final de preparacion configurado. Agregar una nueva ronda despues de Ready devuelve el fulfillment a Preparing de forma explicita y auditable.

Asignacion, salida, entrega, fallo y cancelacion requieren metodos de dominio con estado esperado para detectar carreras. Los eventos registraran actor y hora. No se permitira editar direccion ni cargo despues de `Out for Delivery` salvo una accion administrativa auditada.

### 4. Pago independiente del despacho

`payment_timing` distinguira `Prepaid` y `Cash on Delivery`; `payment_status` distinguira `Unpaid`, `Paid` y `Refunded`. El metodo de pago esperado no equivale a un cobro contable.

En la primera fase:

- pago anticipado reutiliza el pago POS actual;
- contra entrega puede prepararse y despacharse sin `POS Invoice` pagada;
- no se permite cerrar comercialmente la orden como entregada y conciliada mientras el cobro permanezca pendiente;
- la generacion o liquidacion final del comprobante seguira pasando por el flujo POS autorizado.

El momento legal exacto de emision para contra entrega no se cambia en este OpenSpec y debera validarse antes de automatizar la facturacion al despachar o entregar.

### 5. Cargo de delivery como Item

`Restaurant Settings` agregara `delivery_fee_item`, limitado a un Item habilitado para venta y preferiblemente no inventariable. La tarifa manual positiva se agrega o actualiza en una sola linea identificable de `Order Entry Item`. El servidor impedira duplicarla y la excluira de Production Center.

El Item conserva su propia plantilla tributaria y pasa a `POS Invoice` mediante la ruta de items existente. No se agregara un total paralelo que pueda divergir del comprobante.

### 6. Creacion y tablero

`Restaurant Manage` agregara accesos superiores `Salon`, `Delivery`, `Recojo` y `Production Center` sin crear `Restaurant Object` adicionales. El formulario inicial buscara Customer por ID, nombre, tax ID o telefono, reutilizara la creacion DNI/RUC existente y filtrara Address por cliente.

El tablero consultara solo la compania y POS Profile activos, aplicara permisos y mostrara tarjetas por estado con numero, cliente, telefono enmascarado cuando corresponda, zona/distrito, total, pago, platos, tiempo y repartidor. La respuesta sera minima; el detalle personal completo se solicitara solo al abrir la orden.

Al abrir una tarjeta se reutilizara el administrador de productos y orden, desacoplado de la presencia de un `RestaurantObject`. Acciones no aplicables como Transferencia, Divide o Comensales se ocultaran; apareceran acciones de fulfillment.

### 7. Production Center

Los payloads de produccion incluiran `service_type` y una etiqueta preparada en servidor:

- salon: ambiente y mesa;
- delivery: `DELIVERY <orden> | <cliente>`;
- recojo: `RECOJO <orden> | <cliente>`.

Se eliminaran del nuevo flujo las inferencias por prefijo `D` y los filtros visuales basados en `mesas_1`, `mesas_2` o `mesas_3`. Las lineas de cargo de delivery no se enviaran a produccion.

### 8. Direccion y factura

El formulario permite elegir un Address enlazado al Customer o crear uno con los permisos existentes. El servidor verifica la relacion antes de guardarlo. Al facturar se mapearan, cuando correspondan, `customer_address`, `address_display`, `shipping_address_name`, `contact_person` y `contact_mobile` de `POS Invoice` usando campos estandar v15.

La instantanea del fulfillment se conserva aunque el Address maestro cambie. Los payloads realtime no incluiran la direccion completa.

### 9. Concurrencia, idempotencia y realtime

Creacion, tarifa y transiciones aceptaran una clave de cliente o estado esperado. El servidor bloqueara la orden/fulfillment durante mutaciones sensibles y respondera con el estado persistido. Los eventos se publicaran `after_commit` en un canal de fulfillment y los clientes recargaran el tablero de forma acotada.

Un doble clic no podra crear un segundo fulfillment, repetir una transicion ni duplicar el Item de tarifa.

### 10. Permisos y datos personales

- Crear/editar orden: permisos actuales de Table Order mas acceso al POS Profile/Company.
- Ver tablero: roles operativos autorizados y datos minimizados.
- Asignar/despachar: Restaurant Manager, Admin Resto, Cajero o rol configurable posterior.
- Marcar entrega/fallo: mismos roles en fase 1; un rol de repartidor se evaluara en fase 2.
- Cancelar despues de preparacion: requiere motivo y permiso elevado.

Telefono, direccion, tax ID e instrucciones no se escribiran en logs de depuracion ni en eventos globales.

### 11. Migracion y reversibilidad

Un patch idempotente asignara `Dine In` a ordenes existentes sin tipo. No se convertiran mesas `D...` automaticamente. El nuevo Item y sus cuentas no se crearan en silencio: el administrador seleccionara un Item existente o creara/configurara uno mediante el procedimiento normal de ERPNext.

La reversion de codigo deja los nuevos campos y DocTypes sin uso, preservando datos. Antes de retirar metadata se exportaran fulfillments; no se eliminaran pedidos ni facturas.

### 12. Pruebas

| Area | Casos minimos |
|---|---|
| Compatibilidad | orden historica sin tipo, salon normal, mesa obligatoria |
| Creacion | delivery, recojo, cliente existente, nuevo DNI/RUC, direccion ajena rechazada |
| Produccion | enviar, nueva ronda, completar todos, tarifa excluida, etiqueta correcta |
| Logistica | asignar, salir, entregar, fallar, cancelar, transicion invalida, doble clic |
| Pago | anticipado, contra entrega, cobro pendiente, multiples medios actuales |
| Totales | tarifa cero/positiva, impuesto incluido, descuento y factura coincidente |
| Realtime | dos tableros, pestaña oculta, reconexion y reconciliacion |
| Permisos | Guest, mozo, cajero, cocina, gerente, otra compania/POS Profile |
| Regresion | dividir/transferir salon, comensales, precuenta, Production Center y factura |

## Risks / Trade-offs

- **`Table Order` asume mesa en varios metodos:** se introducira un contexto tipado y pruebas antes de habilitar creation delivery.
- **Estados duplicados entre cocina y reparto:** cada estado tendra responsabilidad separada y solo Ready se derivara de produccion.
- **Contra entrega y comprobante:** no se automatizara el momento de emision sin validacion tributaria.
- **Datos personales en realtime:** se usaran tarjetas minimizadas y detalle bajo demanda.
- **Tarifa variable:** usar un Item evita divergencias pero exige configurar correctamente impuestos y cuentas.
- **Interfaz extensa:** el tablero sera una vista separada y no agregara todos los datos a las tarjetas.

## Rollback

1. Deshabilitar los accesos Delivery/Recojo mediante configuracion.
2. Impedir nuevas ordenes externas conservando lectura de las existentes.
3. Revertir assets y codigo al commit anterior.
4. Mantener campos y DocTypes hasta exportar/reconciliar pedidos; no borrar registros por rollback.
5. Restaurar respaldo solo si una migracion de datos produce inconsistencias verificadas.

## Open Questions

- Validar operacionalmente en que momento se emite el comprobante para pago contra entrega: confirmacion, despacho o entrega.
- Definir si el repartidor inicial se modela como User, Employee o Supplier antes de habilitar asignacion nominal.

Estas preguntas no bloquean la primera entrega: el repartidor sera texto/enlace opcional y la facturacion contra entrega conservara el flujo manual actual hasta su aprobacion.
