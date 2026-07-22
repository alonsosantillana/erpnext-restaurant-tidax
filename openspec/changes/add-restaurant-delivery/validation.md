# Validacion v15

Fecha: 2026-07-22  
Sitio autorizado: `v15.local`

## Entorno y respaldo

- Frappe `15.109.0`, ERPNext `15.109.0`, Restaurant Management `1.7.7`.
- Respaldo previo confirmado:
  - `20260721_234008-v15_local-database.sql.gz`
  - `20260721_234008-v15_local-site_config_backup.json`
- `bench --site v15.local migrate` completo; los DocTypes `Restaurant Fulfillment` y `Restaurant Fulfillment Status Log` y el campo `Table Order.service_type` quedaron instalados.
- `enable_delivery` y `enable_pickup` habilitados en el sitio de pruebas.
- La navegación usa un ambiente virtual `Pedidos externos` con tarjetas separadas para Entrega a domicilio y Recojo en local; no crea ambientes ni mesas ficticias en base de datos.
- `delivery_fee_item` permanece sin valor; debe configurarse con un Item de venta no inventariable antes de usar una tarifa mayor que cero.

## Verificaciones automatizadas

- 27 pruebas de `Table Order`: OK.
- 28 pruebas de `Restaurant Object` y Production Center: OK.
- 6 pruebas nuevas de fulfillment, estados y tarifa: OK.
- Smoke test transaccional de Recojo: creación sin mesa, lectura de tablero, cancelación y auditoría: OK; rollback verificado.
- Smoke test transaccional de Delivery: dirección vinculada, tarifa como línea única y total de orden: OK; rollback verificado.
- Python `py_compile`, JavaScript `node --check`, JSON `jq`, `git diff --check`, build de assets y `openspec validate`: OK.

## Configuracion operativa

1. En Restaurant Settings, mantener habilitados Delivery y/o Recojo según la operación.
2. Para cobrar envío, seleccionar `delivery_fee_item`; debe ser un Item habilitado, vendible y no inventariable.
3. La dirección de Delivery debe ser un Address enlazado al Customer.
4. Contraentrega exige un método de pago esperado, pero este no se registra como dinero recibido.

## Pendientes de calificacion manual

- Dos navegadores: altas, cantidades, tablero y cambios logísticos en tiempo real.
- Flujo completo con platos: New, Preparing, Ready, Assigned, Out for Delivery y Delivered.
- Recojo completo hasta Picked Up.
- Pago anticipado y contraentrega con factura/boleta reales y conciliación.
- Comparación de impuestos incluidos, descuentos y tarifa contra POS Invoice.
- Formatos de comanda, precuenta y comprobante con datos mínimos de Delivery.

## Rollback

- Código: revertir los cambios de esta propuesta antes del commit correspondiente.
- Datos: restaurar el respaldo indicado si una migración requiriera reversión integral.
- Configuración: desactivar `enable_delivery` y `enable_pickup` oculta el flujo nuevo sin reinterpretar órdenes de salón.
