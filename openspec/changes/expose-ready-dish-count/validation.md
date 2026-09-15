# Validation

Fecha: 2026-09-15

- OpenSpec `expose-ready-dish-count`: válido en modo estricto.
- ERPNext: 23 pruebas aprobadas.
- La prueba de regresión confirma que solo se suman cantidades con estado `Completed`.
- El contrato OpenAPI conserva 11 rutas, mantiene `version` como `date-time` e incorpora `ready_items_count` como número no negativo.
- Caché limpiada y procesos ERPNext reiniciados correctamente.
- Graphify se ejecutó en modo incremental `--code-only`: 1 archivo reextraído, 2,870 nodos, 4,366 relaciones y 325 comunidades.

