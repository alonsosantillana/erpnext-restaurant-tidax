## Why

La ruta automatica de comprobantes usa `Return POS Invoice`, un formato antiguo
de cuatro pulgadas que no fue disenado para una ticketera de 80 mm. Aunque el
PDF se genera sobre una pagina de 80 mm, el contenido se reduce y pierde
legibilidad al pasar por WebApp Hardware Bridge y el controlador de Windows.

## What Changes

- Agregar un formato fiscal `Restaurant POS Invoice 80mm` con ancho imprimible
  real, tipografia termica y jerarquia visual para totales.
- Mostrar empresa, RUC, comprobante, cliente, lineas, impuestos, descuentos,
  pagos, vuelto, propina separada, estado SUNAT, hash y QR local.
- Crear la configuracion Silent Print homonima para papel de 80 mm.
- Migrar solo configuraciones y rutas que todavia usan
  `Return POS Invoice`; respetar formatos personalizados.
- Usar ESC/POS nativo para las rutas INVOICE y ACCOUNT, y conservar PDF como respaldo
  seleccionable por ruta.

## Impact

- Nuevo Print Format estandar para POS Invoice.
- Nuevo helper Jinja para generar QR SVG local sin servicios externos.
- Nuevo parche v15 idempotente para Silent Print Format y rutas multiempresa.
- Nuevo transporte configurable por ruta y payload RAW auditable en la cola.
- Sin cambios en ventas, SUNAT ni contabilidad.
