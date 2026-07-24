## Sitio

- Sitio autorizado: `v15.local`.
- Migración ejecutada: 2026-07-24.
- Empresa migrada: `ADDERA PERU SAC`.
- POS Profile activo: `Resto`.

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

## Pendiente manual

- Crear o habilitar una segunda empresa operativa con POS Profile propio.
- Crear su `Restaurant Company Settings` con series diferentes.
- Validar dos navegadores simultáneos, realtime, transferencia rechazada entre
  empresas y separación visual de Production Center.
