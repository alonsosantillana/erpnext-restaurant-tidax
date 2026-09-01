## Validation

- `bench --site v15.local migrate --skip-search-index`: correcto; el parche
  `retire_legacy_restaurant_settings` se ejecutó satisfactoriamente.
- Workspace persistido: los enlaces anteriores apuntan a
  `Restaurant Company Settings`.
- Metadatos: los campos `no_imprimir` y `mesas_1/2/3` ya no existen en
  `Restaurant Company Settings`.
- Pruebas específicas de configuración e impresión: 18 pruebas correctas.
- Validación sintáctica: Python, JavaScript y JSON correctos.
- `openspec validate --strict` no puede ejecutarse con el Node.js 18.20.8 del servidor;
  la versión instalada de OpenSpec requiere soporte del modificador RegExp `v` de Node.js 20+.
