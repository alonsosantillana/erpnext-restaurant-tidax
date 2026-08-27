## Sitio

- Sitio autorizado: `v15.local`.
- Migración ejecutada: 2026-07-24.
- Empresa migrada: `ADDERA PERU SAC`.
- POS Profile activo: `Resto`.
- Segunda empresa operativa: `ERPCLOUD SAC`.
- POS Profile de la segunda empresa: `Resto2`.

## Migración

`bench --site v15.local migrate` finalizó correctamente y ejecutó
`restaurant_management.patches.v15_0.migrate_restaurant_company_settings`.

Resultado verificado:

- un registro `Restaurant Company Settings` para `ADDERA PERU SAC`;
- delivery y recojo habilitados como en el Single anterior;
- producto de delivery `CO-SER-064` conservado;
- formatos `Order Account`, `Order` y `Return POS Invoice` conservados;
- cuatro series fiscales conservadas;
- 6 ambientes, 4 mesas y 2 centros de producción asignados a la empresa;
- cero `Restaurant Object` sin empresa.

El patch se ejecutó una segunda vez manualmente. Permaneció un solo registro de
configuración, no duplicó filas hijas y no dejó objetos sin empresa.

## Validaciones automáticas

- Python `py_compile`: correcto.
- JavaScript `node --check`: correcto.
- JSON `jq -e`: correcto.
- `openspec validate make-restaurant-settings-multicompany`: correcto.
- `git diff --check`: correcto.
- `Restaurant Company Settings`: 2 pruebas, correctas.
- `Table Order`: 29 pruebas, correctas.
- `Restaurant Object`: 28 pruebas, correctas.
- Regresión completa con `--skip-test-records`: 65 pruebas, correctas.

La ejecución completa que intenta fabricar fixtures globales se detuvo antes de las
pruebas porque el sitio no contiene el registro estándar `All Supplier Groups`. No es
un fallo del cambio; la misma suite sin creación de fixtures pasó correctamente.

## Runtime

- `get_bootstrap` devolvió empresa `ADDERA PERU SAC` y POS Profile `Resto`.
- `get_rooms` devolvió únicamente los 6 ambientes de esa empresa.
- El resolvedor devolvió la serie de factura `FV-F001-.######` para esa empresa.
- El listener de ambientes devolvió únicamente el ambiente solicitado de la empresa
  activa.
- Tras reforzar los permisos de empresa y la creación de órdenes, la regresión se
  repitió: 65 pruebas, correctas.

## Validación manual multiempresa

Completado y verificado el 2026-07-28:

- `Restaurant Company Settings` independiente para ADDERA y ERPCLOUD;
- POS Profile `Resto` para ADDERA y `Resto2` para ERPCLOUD;
- usuarios `cajero.addera@tidax.pe` y `cajero.erpcloud@tidax.pe`, cada uno
  restringido a su empresa y POS Profile;
- apertura `POS-OPE-ADA-2026-00001` para el cajero ADDERA;
- apertura `POS-OPE-ECS-2026-00002` para el cajero ERPCLOUD;
- ERPCLOUD con 2 ambientes, 4 mesas y 2 centros de producción;
- P3 cubre `PLATOS CALIENTES`, `PLATOS FRIOS` y `ENTRADAS`;
- P5 cubre `BEBIDAS`;
- dos sesiones separadas muestran los ambientes de su empresa sin mezcla visual.

## Pendiente manual

- Ejecutar en ambas empresas el flujo mesa, orden, envío a cocina, cambio de estados,
  cuenta, pago y creación de POS Invoice.
- Comparar impuestos incluidos, descuentos y totales entre Table Order y POS Invoice.
- Probar Boleta y Factura con sus series fiscales por empresa.
- Verificar impresión de comanda, cuenta, boleta y factura mediante Silent Print.
- Validar realtime de órdenes y Production Center entre navegadores.
- Intentar una transferencia cruzada y confirmar su rechazo sin cambios parciales.

## Series independientes de órdenes (2026-08-26)

- ADDERA configurada con `OR-ADA-.YYYY.-.#####`.
- ERPCLOUD configurada con `OR-ECS-.YYYY.-.#####`.
- Las órdenes existentes `OR-2026-00004` y `OR-2026-00005` conservaron sus nombres.
- Patch `set_company_table_order_series` ejecutado correctamente mediante migrate.
- Hook `Table Order.autoname` verificado en runtime.
- `test_pos_series`: 9 pruebas correctas.
- `Table Order`: 32 pruebas correctas.
- `Restaurant Company Settings`: 4 pruebas correctas.
- JSON, Python, `git diff --check` y OpenSpec estricto: correctos.
