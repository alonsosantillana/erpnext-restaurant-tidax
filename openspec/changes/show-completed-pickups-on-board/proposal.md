## Why

El tablero muestra una columna Recogido pero su consulta excluye los fulfillments
Picked Up + Paid. Al recoger un pedido prepagado desaparece y el contador de la
columna queda en cero, aunque la transición esté auditada correctamente.

## What Changes

- Añadir un selector de fecha para recogidos pagados, inicialmente hoy.
- Conservar pendientes de cualquier fecha y añadir los recogidos pagados del día
  seleccionado según el historial de transición, no creation ni modified.
- Mantener el contador de pendientes independiente de las tarjetas finalizadas.
- Preservar Delivery, permisos, contexto de compañía/POS e include_closed=1.
- Probar consulta y comportamiento frontend sin conectar a un sitio operativo.

## Impact and acceptance

Solo restaurant_management en desarrollo. API de lectura get_fulfillment_board,
FulfillmentBoard JS/CSS, pruebas y documentación. Riesgo medio: selección de filas
y contadores; no modifica pedidos, cobros, impuestos, estados, configuración,
esquema, permisos, hooks, fixtures o apps externas. No migrate ni despliegue.

Recogido pagado del día aparece sin aumentar pendientes; recogido ayer modificado
hoy no aparece como recogido de hoy; pendientes antiguos siguen visibles. Cambiar
fecha o recibir realtime respeta la selección y no acepta respuestas obsoletas.
