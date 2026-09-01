# Tareas

## Especificación

- [x] Documentar alcance operativo, exclusión contable y riesgo multiempresa.
- [x] Definir modelo, validaciones, migración y matriz de pruebas.

## Implementación

- [x] Añadir campos multiempresa y de caja a `Resto Gastos`.
- [x] Añadir serie de gastos a `Restaurant Company Settings`.
- [x] Implementar correlativo y validaciones autoritativas en servidor.
- [x] Mejorar filtros y valores derivados del formulario.
- [x] Corregir el filtro de compañía del reporte de cierre.
- [x] Añadir patch para series de configuraciones existentes.

## Verificación

- [x] Validar JSON, JavaScript y Python.
- [x] Ejecutar pruebas unitarias de validaciones y series.
- [ ] Ejecutar `openspec validate make-resto-gastos-multicompany`.
- [x] Ejecutar migrate autorizado en `v15.local`.
- [ ] Probar creación, envío, cancelación y reporte en ambas empresas.
