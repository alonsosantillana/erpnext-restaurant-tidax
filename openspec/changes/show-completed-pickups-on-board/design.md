## Context and architecture

Graphify identifica get_fulfillment_board y su contexto autenticado; se corroboró
en api.py, FulfillmentBoard y RestaurantFulfillment._transition. El filtro actual
excluye terminal + Paid. El frontend crea la columna terminal pero obtiene sus
badges operativos del tamaño de la lista al recargar, mezclando dos conceptos.

## Server

Agregar completed_date opcional a get_fulfillment_board. Sin ese argumento se
mantiene el contrato previo; include_closed=1 conserva su consulta histórica.
El frontend Pickup enviará fecha ISO, inicialmente hoy según system_datetime de
Frappe (zona del sitio, no del usuario ni del reloj local del navegador).
El día se interpreta como fecha del sitio, igual que changed_at=now_datetime del
historial. Validar formato y límites antes de consultar. Delivery no cambia.

Con fecha y Pickup, unir dos consultas permission-aware sobre Restaurant Fulfillment:
la de pendientes existente (sin límite de fecha) y una de Picked Up + Paid filtrada
por child Restaurant Fulfillment Status Log, to_status=Picked Up y changed_at >=
inicio y < día siguiente. Ambas usan Company/POS activos y get_list, sin SQL nuevo.
Distinct y deduplicación por parent impiden tarjetas repetidas. Consultas separadas
evitan que cerrados desplacen pendientes; cada una conserva el límite operativo
existente de 200 filas. El payload sigue siendo una lista mínima y el enriquecimiento
de importes sigue restringido a las órdenes de esos padres.

No se inventa fecha para históricos sin evento Picked Up. Los recogidos sin pagar
siguen pendientes aunque sean de otra fecha. get_fulfillment_counts no se modifica:
terminal + Paid no incrementa sus contadores; no depende de fecha ni paginación.

## Client

Selector accesible «Recogidos del día», visible solo en Pickup, fecha inicial hoy.
La fecha limita solo recogidos pagados, no pedidos pendientes anteriores. Cambiar
fecha dispara consulta y realtime/polling conservan selección. Capturar tipo/fecha
y número de solicitud para ignorar respuestas antiguas o de vistas ocultas.
Eliminar counts[type]=rows.length y consultar get_fulfillment_counts tras reload.
Render sigue agrupando por estado: la columna Recogido cuenta tarjetas visibles,
el badge/hub superior cuenta pendientes. CSS acotado para una barra compacta.

## Scope, permissions and rollback

Archivos: api.py, public/restaurant/js/fulfillment-board-class.js,
public/restaurant/css/fulfillment-board.css, nuevas pruebas Python/Node y documentación.
Sin migración, DocTypes, fixtures, hooks, permisos, endpoints nuevos o escrituras.
No ejecutar bench run-tests en sitio operativo, migrate, build, restart ni push
durante implementación. El despliegue/frontend se autorizará por separado.

Revisión especializada obligatoria realizada antes de implementar. Rollback:
revertir únicamente el futuro commit de fix/pickup-completed-board y actualizar
assets/procesos mediante despliegue autorizado; sin datos que restaurar.

## Test matrix

Defaults heredados, fecha válida/inválida, include_closed=1 y Delivery sin cambios;
recogido hoy, ayer modificado hoy, creado ayer recogido hoy, día siguiente a las
00:00 excluido, duplicados, pendientes antiguos, cancelado, no permiso/Guest,
aislamiento Company/POS en ambas consultas. Node: selector, args, agrupado,
contador autoritativo independiente de filas, realtime y respuesta fuera de orden.
Integración ORM real/permisos, timezone del sitio, dos navegadores y validación
visual quedan para sitio desechable/despliegue autorizado.
