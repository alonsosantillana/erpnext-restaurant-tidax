## Architecture
Mantener _queue, cola short, IDs, enqueue_after_commit y deduplicación. Los cinco productores usan callback_event dentro de kwargs; send_callback resuelve el alias con validación explícita antes de leer documentos. event sigue compatible con llamadas directas.
## Analysis and Reuse
Se consultó el grafo Graphify local y se verificaron service.py, client.py y hooks.py. Se reutilizan test_service.py, test_callbacks.py y el receptor independiente desarrollado previamente. La firma instalada de frappe.enqueue confirma la colisión. No se regenera el grafo por un cambio sin estructura nueva de producción.
## Affected Components
service.py, test_callback_queue.py, herramientas de verificación y documentación. DocTypes PedidosYa Order y PedidosYa Integration Settings se usan solo como fixtures nuevos en v15.local. Sin cambios de esquema, permisos, hooks, APIs públicas, reportes o datos existentes.
## Testing
Pruebas unitarias con enqueue instalado y HTTP simulado. Integración en v15.local: receptor HTTPS temporal en loopback, certificado CA confiado solo por el proceso de prueba, credenciales ficticias y evidencia saneada. RQ Worker real en cola exclusiva; el harness redirige solo la selección de cola en memoria, conservando serialización y execute_job. El job programado se invoca de forma dirigida, sin habilitar el cron general; no se presenta como ciclo natural.
## Safety
No usar bench run-tests por sus fixtures globales. Baseline de configuraciones, registros existentes y conteos operativos. Todos los inbox test_order=1, sin Table Order ni fulfillment. Settings nuevos deshabilitados para entrada. Retirar URLs y limpiar solo la caché ficticia al terminar, incluso ante fallo. Modo developer desactivado solo en memoria del proceso de prueba para impedir trazas con variables sensibles. No contactar producción ni receptor público.
## Risks
Los jobs ya serializados con event perdido no quedan reparados: requerirán análisis separado antes de producción. Fallos HTTP no deben marcar notificación. La prueba de preparado/recogido no crea fulfillment; sus productores se cubren con dobles de prueba. El cliente actual no renueva tras 401; se verifica su comportamiento, sin ampliarlo.
## Rollback
Rama fix/pedidosya-callback-queue desde master 8ae5eaf. Revertir el commit de corrección en desarrollo si fuera necesario. Sin migración inversa ni restauración de base de datos. Conservar fixtures cerrados para auditoría; detener únicamente los procesos temporales creados por el harness.
