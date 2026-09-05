# Cambio: hacer recuperable la emisión electrónica del POS restaurante

## Problema

El pago confirma la Factura POS y luego depende de una segunda petición síncrona del navegador para consultar y enviar a Nubefact. Si esa petición se interrumpe, la venta queda pagada localmente, la interfaz permanece esperando y el comprobante no tiene un estado recuperable.

## Solución

- Marcar la Factura POS electrónica con un estado de emisión persistente.
- Encolar el envío después del commit de la orden y la factura.
- Consultar Nubefact antes de cada intento de generación.
- Recuperar periódicamente trabajos en cola, fallidos o abandonados.
- Mantener la interfaz operativa y consultar el resultado sin bloquearla.
- Registrar solamente errores sanitizados y nunca credenciales ni payloads fiscales.

## Alcance

Solo se recuperan automáticamente Facturas POS electrónicas iniciadas por Restaurant Manage. Los comprobantes históricos sin la nueva marca no se envían automáticamente.
