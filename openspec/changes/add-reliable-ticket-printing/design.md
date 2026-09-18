## Context

La estacion habitual es una caja Windows 10/11 con HWB enlazado a
`127.0.0.1:12212`. La configuracion observada mapea ORDER, ACCOUNT e INVOICE a
una POS-80-Series. Comandas y cocina son opcionales; los comprobantes
electronicos son el flujo obligatorio.

HWB confirma entrega al spooler mediante el identificador solicitado. Esa
respuesta no demuestra salida fisica de papel. Por ello el dominio usa
`Accepted by HWB` y nunca `Printed` como estado automatico.

## Decisions

### Ownership

silent_print mantiene permisos, PDF y transporte WebSocket. Restaurant
Management conserva la cola durable y el enrutamiento empresarial.

### Station and lease

Cada estacion pertenece a una Company y tiene un usuario receptor. La pagina de
estacion registra un identificador de cliente, version HWB y heartbeat. Solo una
sesion con lease vigente puede reclamar trabajos de esa estacion.

### Durable jobs

Restaurant Print Job almacena metadatos, nunca PDF base64. La estacion reclama
un lote pequeno, solicita el PDF al servidor, lo envia a HWB con el nombre del
job como id y registra el acuse.

Estados: Pending, Sending, Accepted by HWB, Failed, Ambiguous y Cancelled.

Una respuesta negativa confirmada puede reintentarse de forma controlada. Un
timeout posterior a `websocket.send()` produce Ambiguous y exige reimpresion
manual para evitar duplicados.

### Routing

Las rutas pertenecen a Restaurant Company Settings. Tipos iniciales:

- INVOICE: comprobante electronico;
- ACCOUNT: precuenta;
- ORDER: comanda general;
- KITCHEN: ticket de centro de produccion.

Una ruta define estacion, formato, print type, copias, habilitacion y automatismo.
Las rutas de cocina pueden limitarse a un Production Center.

### Trigger points

- INVOICE se encola solamente despues de persistir el POS Invoice y completar
  el flujo electronico que ya usa la aplicacion.
- ACCOUNT se solicita explicitamente desde el boton Cuenta.
- ORDER/KITCHEN se encolan al enviar una ronda nueva, nunca por cambios de estado.

### Immutable order rounds

Every press of Order assigns one ordered_nro to the dishes that were still
Attending. The durable ORDER job stores that batch number. PDF rendering reloads
the Table Order and exposes only entries from the stored batch to the Order
Print Format. The browser does not enqueue a second request after the send
response; the server creates the job in the same business operation and treats
printing failures as non-blocking.

The ORDER route uses native ESC/POS output for a high-contrast 80 mm kitchen
ticket. It does not include prices and emphasizes quantity, dish, production
center and notes with printer-native bold and double-size commands. The PDF
Order Print Format remains an 80 mm fallback, but existing ORDER routes migrate
to ESC/POS to avoid raster scaling and reduced thermal-print clarity.

### Compatibility

La estacion acepta el acuse normalizado por silent_print para HWB 0.13.0 y
1.0.1. La migracion no obliga a actualizar el ejecutable, pero se recomienda
probar 1.0.1 por su correccion del limite Base64.

## Rollback

Deshabilitar estaciones/rutas devuelve los botones al flujo de vista previa sin
eliminar ordenes ni comprobantes. Los nuevos DocTypes son aditivos y sus
registros pueden conservarse como auditoria. Revertir assets restaura el cliente
anterior; no se borran configuraciones existentes de silent_print.
