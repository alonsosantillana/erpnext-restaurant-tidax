## Sitio

- Sitio: `v15.local`.
- Migración ejecutada correctamente.
- Patch `set_company_pos_entry_series` ejecutado en 0.148 s.

## Configuración

- ADDERA: `POS-OPE-ADA-.YYYY.-.#####` y
  `POS-CLO-ADA-.YYYY.-.#####`.
- ERPCLOUD: `POS-OPE-ECS-.YYYY.-.#####` y
  `POS-CLO-ECS-.YYYY.-.#####`.
- Custom Fields de solo lectura creados en apertura y cierre POS.
- No existen Document Naming Rules para esos DocTypes que interfieran con los hooks.

## Prueba funcional

Se ejecutó `set_new_name` dentro de transacciones revertidas para no crear documentos
ni consumir contadores:

- ADDERA: `POS-OPE-ADA-2026-00001` y `POS-CLO-ADA-2026-00001`.
- ERPCLOUD: `POS-OPE-ECS-2026-00001` y `POS-CLO-ECS-2026-00001`.

## Pruebas

- 5 pruebas unitarias nuevas: correctas.
- Regresión completa de `restaurant_management`: 70 pruebas, correctas.
- Python, JavaScript, JSON y `git diff --check`: correctos.
- OpenSpec: válido.

ERPCLOUD todavía necesita un POS Profile propio para insertar una apertura POS real;
la resolución y nomenclatura independiente ya fueron verificadas sin persistir
documentos.
