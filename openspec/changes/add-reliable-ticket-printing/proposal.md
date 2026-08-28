## Why

La impresion actual depende de una pestana global, llamadas directas y eventos
Realtime sin cola durable. Una desconexion de navegador, HWB o Windows puede
perder el trabajo; un reintento ciego puede duplicar una comanda o comprobante.
La configuracion tampoco separa estaciones y rutas por empresa.

## What Changes

- Agregar estaciones de impresion por empresa con usuario receptor y heartbeat.
- Agregar rutas para comprobante, precuenta, comanda general y cocina.
- Persistir cada solicitud en Restaurant Print Job con clave idempotente,
  intentos, acuse HWB y error controlado.
- Incorporar una pagina de estacion para Windows 10/11 que procese la cola a
  traves de silent_print y HWB 0.13.0 o 1.0.1.
- Centralizar comprobantes, precuentas y comandas en el nuevo servicio.
- Mantener venta, orden y comprobante independientes de fallos de impresion.

## Impact

- Nuevos DocTypes: Restaurant Print Station, Restaurant Print Route y
  Restaurant Print Job.
- Restaurant Company Settings recibe rutas y opciones automaticas.
- Se reemplazan llamadas directas desde el cliente por APIs de cola.
- Se agrega una pagina Desk para la estacion permanente de caja.
- Dependencia operativa: silent_print endurecido y HWB local.
