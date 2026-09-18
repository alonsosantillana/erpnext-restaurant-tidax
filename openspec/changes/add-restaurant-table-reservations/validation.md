## Validación ejecutada

- `openspec validate add-restaurant-table-reservations --strict` con Node.js 20:
  correcto.
- Compilación Python de controladores, configuración, parche e instalación:
  correcta.
- `node --check` de formulario, calendario, lista y Restaurant Manage: correcto.
- Validación `jq` de DocTypes, workspace, página, ajustes y fixtures: correcta.
- Pruebas unitarias nuevas de reservas: 5/5 correctas.
- Pruebas unitarias de series, incluida `RES-ECS-.YYYY.-.#####`: 13/13
  correctas.
- Regresión aislada de mesas, ajustes, reservas y series: 59 pruebas correctas y
  3 pruebas heredadas no ejecutables por no existir compañía predeterminada en la
  sesión del runner; fallan antes de alcanzar el código modificado.
- `git diff --check`: correcto.
- Graphify `extract --code-only` y `cluster-only`: grafo y reporte actualizados.

## Validación pendiente de despliegue

- Ejecutar `bench --site <sitio> migrate` para sincronizar DocTypes, campos, rol y
  parche de serie.
- Validar manualmente crear, confirmar, registrar llegada, sentar, facturar y
  cancelar una reserva en un sitio migrado.
- Probar dos sesiones concurrentes intentando reservar o sentar la misma mesa.

No se ejecutó `bench run-tests` contra `v15.local` para evitar la limpieza de datos
de prueba que anteriormente eliminó precios del POS.
