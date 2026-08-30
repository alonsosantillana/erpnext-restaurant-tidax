## Context

`PayForm.make_inputs()` recorre `RM.pos_profile.payments` y construye un input
permanente por medio. `payments_values` y `update_paid_value()` vuelven a recorrer
esos inputs para formar el mapa enviado a `Table Order.make_invoice`.

Graphify ubica estas funciones, el teclado `NumPad`, la seccion independiente de
propina y `send_payment()` dentro de la misma comunidad `PayForm`. La revision del
codigo confirma que fuera de esta clase ningun consumidor depende de la coleccion
DOM `payment_methods`; el servidor solo recibe el mapa final.

## Goals / Non-Goals

**Goals:**

- mantener una altura estable con cualquier cantidad de medios configurados;
- conservar cobros simples y mixtos, el teclado y el contrato servidor actual;
- hacer visible la distribucion, el saldo pendiente y el cambio;
- mantener accesibilidad basica mediante labels, botones y no depender del color.

**Non-Goals:**

- cambiar conciliacion, impuestos, propinas, POS Invoice o envio electronico;
- modificar configuracion de medios, cuentas o permisos;
- aceptar sobrepagos que la validacion actual rechaza.

## Decisions

### Estado de asignaciones separado del DOM

`PayForm` mantendra `payment_allocations`, un objeto en memoria indexado por nombre
de medio. Solo los importes positivos se exponen en `payments_values`. Esto evita
crear inputs ocultos y mantiene exactamente el payload actual.

Alternativa descartada: conservar un input invisible por medio. Reduciria el
cambio interno, pero mantendria estado duplicado y haria mas fragil la
sincronizacion entre selector, resumen e inputs.

### Un editor activo y resumen compacto

La seccion tendra:

- selector con todos los medios autorizados por el perfil;
- un importe activo conectado al `NumPad`;
- accion `Agregar otro medio` que elige el siguiente medio sin asignacion;
- lista compacta solo de asignaciones positivas, con editar y eliminar;
- linea de Pagado, Pendiente y Cambio.

Cambiar el selector carga la asignacion existente o, para un medio nuevo, el saldo
pendiente positivo. Editar el importe actualiza inmediatamente el objeto y el
resumen. La lista usa botones explicitos para teclado/touch.

Alternativa descartada: un modal secundario para pagos mixtos. Ahorraria espacio
en el formulario principal, pero agregaria pasos y ocultaria la distribucion
durante el cobro.

### Preservar el contrato fiscal

`send_payment()` seguira comparando la suma de `payments_values` con
`payable_amount` usando la tolerancia existente. El objeto enviado, la propina y
la llamada `make_invoice` no cambian.

No se modifica codigo Python, DocTypes, hooks, fixtures, reportes ni dependencias.
Tampoco cambian series, descuentos, gratuidad, impuestos o campos SUNAT.

### Estilos aislados

Se agregara `pay-form.css` a los assets explicitos de Restaurant Manage. Las
clases se limitaran al formulario compacto, con lista de altura maxima y scroll
para evitar crecimiento ilimitado incluso en pagos mixtos excepcionales. En el
modal de escritorio, pagos y teclado ocuparan columnas adyacentes con teclas
uniformes; en una pantalla estrecha se apilaran sin desbordamiento.

### Helpers verificables

La normalizacion de importes y calculo de pagado/pendiente/cambio se implementaran
como funciones puras exportables solo cuando exista CommonJS. Esto permite pruebas
con `node --test` sin introducir una dependencia de testing ni alterar el browser.

## Permissions, Transactions and Concurrency

No se agregan permisos ni endpoints. Los medios provienen del POS Profile ya
autorizado de la compania activa. Todo el estado nuevo vive en el modal del
cliente; la transaccion definitiva y las validaciones servidor permanecen en
`Table Order.make_invoice`.

No se agrega realtime: si cambia el POS Profile, el listener existente cierra el
formulario para evitar pagar con una configuracion obsoleta.

## Migration and Deployment

- No requiere migracion ni patch de datos.
- Requiere `bench build --app restaurant_management` y limpieza de cache para
  publicar el JavaScript y CSS.
- `bench restart` solo sera necesario si el entorno no recarga assets correctamente.

## Risks / Trade-offs

- **Importe sobrescrito al cambiar de medio** -> conservar siempre la asignacion
  por nombre y cargarla al regresar.
- **Eventos recursivos al rellenar el input** -> distinguir actualizaciones de UI
  de eventos introducidos por el usuario.
- **Error por redondeo** -> normalizar a dos decimales para la presentacion y
  conservar la tolerancia de conciliacion existente al enviar.
- **Sin espacio con muchos pagos realmente usados** -> lista con altura maxima y
  scroll; los medios no usados nunca crean filas.
- **Regresion en propina** -> mantener su seccion y payload sin cambios y cubrirla
  en la prueba manual.

## Test Matrix

| Area | Case | Expected |
|---|---|---|
| Default | un medio predeterminado | seleccionado con saldo total |
| Fallback | ningun predeterminado | primer medio seleccionado |
| Simple | un medio cubre total | mapa con una entrada |
| Mixed | efectivo parcial + banco | dos entradas y pendiente cero |
| Edit | volver a medio usado | carga y actualiza, no duplica |
| Delete | eliminar asignacion | recalcula pendiente |
| Keypad | editar importe activo | cambia solo el medio seleccionado |
| Validation | suma distinta | bloquea antes de facturar |
| Tip | venta + propina | propina separada, venta concilia sola |
| Scale | diez medios disponibles | altura estable, todos seleccionables |
| Company | perfiles distintos | cada cajero ve solo sus medios cargados |

## Rollback

Revertir `pay-form-class.js`, `pay-form.css` y la inclusion del asset restaura el
formulario anterior. No hay esquema ni datos que revertir, y las facturas ya
generadas no se alteran.
