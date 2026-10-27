# TIDAX — Corrección de callbacks PedidosYa en desarrollo

## Resultado
Corrección aplicada y validada únicamente en el entorno de desarrollo, sitio de prueba v15.local. Sin despliegue ni conexión a producción durante esta fase.

La colisión con el argumento reservado event de frappe.enqueue impedía ejecutar send_callback. Los cinco productores ahora envían callback_event como argumento del método. El handler mantiene event posicional y nombrado para compatibilidad, y rechaza eventos ausentes, desconocidos o contradictorios antes de acceder a documentos.

## Trazabilidad
- App: restaurant_management.
- Rama principal: master, base 8ae5eaf, sincronizada con upstream/master al iniciar.
- Rama de trabajo: fix/pedidosya-callback-queue.
- OpenSpec: openspec/changes/fix-pedidosya-callback-queue, validación estricta.
- Análisis: grafo Graphify local contrastado con service.py, client.py y hooks.py; revisión especializada de integración y QA.
- Código funcional modificado: restaurant_management/integrations/pedidosya/service.py.
- Nuevos: test_callback_queue.py, tools/verify_pedidosya_callbacks_dev.py, especificación y este informe con evidencia saneada.
- Sin archivos eliminados, cambios de esquema, hooks, permisos o apps core.

## Pruebas unitarias
54 pruebas del paquete PedidosYa aprobadas mediante unittest, sin base de datos, Redis o HTTP externos. Se evitó bench run-tests y sus fixtures generales.

La regresión usa frappe.enqueue instalado y ejecuta los cinco productores reales: aceptar, rechazar, preparado, recogido y recuperación (aceptado/rechazado). Comprueba encolado después del commit, transporte del evento, IDs y argumentos de rechazo. Cubre los cuatro contratos HTTP y las formas callback_event, event nombrado y event posicional, así como eventos inválidos y fallo HTTP sin confirmación.

## Integración real en desarrollo
Se reutilizó el receptor independiente existente en una instancia temporal HTTPS de loopback, con credenciales ficticias y SQLite propios. El certificado se confió solo dentro del proceso de prueba; la confianza del sistema rechazó el certificado y nunca se desactivó la validación TLS.

Un Worker RQ real consumió una cola privada. El harness redirige get_queue(short/default) en memoria a esa cola; los productores, serialización, execute_job y envío HTTP de la aplicación permanecen reales. No se escucharon ni drenaron colas compartidas.

El scheduler general permaneció pausado/deshabilitado. Se ejecutó únicamente ScheduledJobType.enqueue(force=True) para recover_pending_orders: cinco ejecuciones dirigidas, no ciclos naturales del cron. El desarrollo no acredita aún la ejecución del cron corregido en producción.

| Caso | Resultado |
|---|---|
| accepted, rejected, prepared, picked_up mediante workers | HTTP 204 y bandera notificada |
| prepared | Sin cuerpo, validado por el receptor real |
| accepted/rejected transitorios | 503 en primera recuperación, 204 en segunda |
| Recuperación posterior al éxito | No vuelve a enviar callbacks confirmados |
| accepted/rejected persistentes | Dos recuperaciones con 503; banderas sin confirmar |
| Contraseña ficticia incorrecta | Login 401 y bandera sin confirmar; restaura tras corregir solo el setting ficticio |
| Token inválido | 401 en dos intentos; no renueva automáticamente; recupera tras limpiar solo su caché ficticia |
| Token vencido | 401; recupera tras limpiar solo su caché ficticia |

La prueba produjo 16 IDs RQ distintos. Los IDs estables del job programado y de recuperación se reutilizan entre ejecuciones; no equivalen al total de ejecuciones. La evidencia incluye fechas, estados y recepciones saneadas.

## Integridad y cierre
Cada ejecución completa creó once PedidosYa Order test_order=1 y un setting exclusivo deshabilitado. Se realizaron dos ejecuciones completas; quedan 22 inbox ficticios y dos settings cerrados para auditoría. Un ensayo adicional falló deliberadamente antes del primer commit y revirtió sus inserciones. No se invocó dispatch, process_order, aceptación/rechazo operativo ni transiciones de fulfillment durante la integración real; esos productores se cubrieron con dobles unitarios.

Al terminar se retiraron todas las URLs ficticias, se limpió únicamente su clave de caché y se detuvo el receptor temporal. Cola privada vacía, sin trabajos en ejecución. Configuración y registros existentes, archivos de configuración y habilitación del scheduler permanecen sin cambios. Los fixtures cerrados se conservan para auditoría.

Los conteos de órdenes, fulfillment, facturas, pagos, inventario, contabilidad y precios se mantuvieron sin cambios. La evidencia detallada se conserva en el repositorio corporativo interno.

La revisión especializada exigió verificar pausa efectiva del scheduler y reforzar la limpieza frente a errores. Ambas mejoras se implementaron. Un fallo deliberado antes del primer commit confirmó rollback, parada del receptor, restauración de la CA y conservación de evidencia, sin cambios en registros existentes. La integración completa volvió a pasar con el harness final.

El modo developer se desactivó solo en memoria de los procesos de prueba para evitar trazas con variables sensibles. No se exportaron contraseñas, tokens, cuerpos o configuraciones privadas.

## Límites y riesgos pendientes
- El cliente actual no invalida ni renueva inmediatamente un token tras HTTP 401. Se verificó ese comportamiento, sin ampliar el alcance de esta corrección.
- Los jobs antiguos ya serializados sin evento no se reparan al cambiar el código. Antes de un despliegue habrá que revisar los pendientes y planificar su recuperación.
- Preparado y recogido se probaron por HTTP/worker real sin crear documentos operativos. La recuperación ligada a fulfillment real queda fuera de esta validación.
- El receptor simulado no sustituye el sandbox ni la certificación oficial de PedidosYa.
- Producción sigue con su versión anterior; cualquier despliegue requiere autorización específica.

## Reproducción
Pruebas unitarias desde la raíz de la app:
    /home/erpnext/frappe-bench/env/bin/python -B -m unittest discover -s restaurant_management/integrations/pedidosya -p 'test_*.py'

Integración opcional solo en desarrollo, desde /home/erpnext/frappe-bench/sites:
    TDX_DEV_EVIDENCE=/ruta/nueva/result.json /home/erpnext/frappe-bench/env/bin/python -B ../apps/restaurant_management/tools/verify_pedidosya_callbacks_dev.py

Requiere el repositorio y entorno virtual local del receptor existente. Genera nuevos fixtures ficticios y los cierra automáticamente. No habilita el scheduler.

## Reversión
Revertir únicamente el commit de esta rama en desarrollo si fuera necesario. No requiere migración inversa, restauración de base de datos ni borrado de documentos operativos. Mantener fixtures cerrados para auditoría. Sin merge a master ni despliegue hasta aprobación posterior.

## Respaldo y publicación
La rama se conserva localmente con respaldo recuperable, sin merge a master. La publicación en upstream queda pendiente de autorización explícita por tratarse de un repositorio público. El repositorio de la app es público; su informe y JSON de validación contienen solo evidencia técnica saneada. Los conteos comerciales detallados se conservan exclusivamente en la carpeta interna TIDAX. No existen workflows de despliegue versionados en este repositorio.
