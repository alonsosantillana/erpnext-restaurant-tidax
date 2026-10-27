## Diagnosis and scope

Servidor confirmado 192.168.2.53. Solo restaurant_management; inicio master
7fe18ef, sincronizado y sin cambios. Rama de trabajo fix/pickup-completed-board.
Autorización del usuario: ajustar la columna Recogido, todo en desarrollo.

La API omitía Picked Up + Paid y el frontend contaba filas como pendientes. Ahora
el tablero Pickup envía fecha del sitio y muestra recogidos pagados auditados en
esa fecha, sin excluir pendientes anteriores ni inflar los badges operativos.
Se conserva el contrato anterior cuando no se proporciona completed_date y cuando
include_closed=1. Delivery conserva su selección anterior. No se modificaron
estados, pagos ni comprobantes existentes.

## Files

Modificados: api.py, public/restaurant/js/fulfillment-board-class.js,
public/restaurant/css/fulfillment-board.css y docs/pedidosya-integration.md.
Creados: test_fulfillment_board.py, public/restaurant/js/test_fulfillment_board.js,
y los cinco documentos OpenSpec de este cambio. Ningún archivo eliminado.
No se modificaron otras apps, DocTypes, hooks, fixtures, permisos o configuración.

## Automated validation

Ejecutado desde la raíz de restaurant_management:

```bash
PYTHONDONTWRITEBYTECODE=1 ../../env/bin/python -m unittest \
  restaurant_management.test_fulfillment_board \
  restaurant_management.restaurant_management.doctype.table_order.test_invoice_payments \
  restaurant_management.test_order_panel_layout -q
PYTHONDONTWRITEBYTECODE=1 ../../env/bin/python -m unittest discover \
  -s restaurant_management/integrations/pedidosya -p 'test_*.py' -q
/home/erpnext/.nvm/versions/node/v20.20.2/bin/node --test \
  restaurant_management/public/restaurant/js/test_fulfillment_board.js \
  restaurant_management/public/restaurant/js/test_pay_form.js \
  restaurant_management/restaurant_management/page/restaurant_print_console/test_restaurant_print_console.js
```

Resultado: 31 + 44 pruebas Python y 23 Node aprobadas, total 98. Incluyen 14 nuevas
de consulta y 9 nuevas frontend. Conexión de sitio bloqueada y DB/consultas simuladas
en la suite nueva. Node usa VM y DOM simulado, sin navegador ni HTTP.

Cobertura nueva: día auditado en vez de creation/modified, fronteras de medianoche,
fechas inválidas, recogidos sin pagar y pendientes de días anteriores, cancelados,
company/POS y acceso simulados, deduplicación, límites independientes, backward
compatibility y Delivery. Frontend: fecha del sitio (diferente de la del usuario),
selector, agrupación, contadores autoritativos, realtime/polling y rechazo de
respuestas antiguas al cambiar fecha/tipo/visibilidad.

- AST Python y node --check correctos; no bytecode generado.
- git diff --check correcto; OpenSpec estricto válido antes y después de implementar.
- Revisión especializada del diff sin bloqueantes. La herencia de permisos padre
  en JOIN del child, calificación de campos y DISTINCT se corroboraron en Frappe v15.
- Graphify consultado y reconstruido solo con código local, sin IA remota; sus
  artefactos permanecen ignorados por Git. No se instalaron hooks o herramientas.

## Limits and pending tests

No se ejecutó ORM/MariaDB real, un navegador real, un sitio desechable, ni tests
bench. Los mocks prueban filtros y contrato, no equivalen a integración de SQL y
permisos reales. Se mantienen 200 filas por consulta: hasta 200 pendientes y
200 recogidos pagados del día, sin que estos desplacen los primeros. Registros
Picked Up sin historial auditado no usan modified como sustituto de fecha.

No se accedió ni desplegó en resto.v1.tidax.pe. No se ejecutaron migrate, build,
clear-cache, restart, console, escritura de datos o pruebas que inicialicen ERPNext
y puedan borrar Item Price. No hace falta migrate por este ajuste sin esquema.

Tras publicar/desplegar con autorización, actualizar los assets según el proceso
habitual y recargar Restaurant Manage. Validar con dos navegadores:

1. Contexto Company/POS correcto; fecha inicial corresponde al sitio.
2. Seleccionar el día del evento Picked Up de un fulfillment pagado existente:
   debe aparecer en Recogido, sin incrementar el badge de pendientes.
3. Elegir otro día: recogidos pagados cambian; pendientes anteriores permanecen.
4. Confirmar transición en otra sesión: tarjeta y contadores se reconcilian sin F5.
5. Revisar un usuario sin acceso, otro perfil/empresa y Delivery sin cambios.

Estas validaciones quedan pendientes en tasks.md; no se declara certificación
completa ni verificación visual del despliegue.

## Git handoff and rollback

La implementación se entregó inicialmente sin commit, merge o push. Posteriormente
el usuario autorizó «ok pasa los cambios a la rama principal y push remoto».
Se repitieron las 98 pruebas aisladas y OpenSpec estricto antes de preparar commit,
integración en master y publicación en upstream (alonsosantillana/erpnext-restaurant-tidax).
La autorización de publicación no incluye despliegue ni cambios de sitios.
Revertir solo el commit de esta corrección y refrescar assets/procesos mediante
despliegue autorizado; no hay esquema, precios o pedidos que restaurar.
