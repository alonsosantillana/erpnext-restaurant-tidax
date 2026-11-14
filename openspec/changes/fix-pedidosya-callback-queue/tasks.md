## 1. Análisis
- [x] 1.1 Revisar código, OpenSpec, grafo local, entorno y autorización solo desarrollo.
- [x] 1.2 Obtener revisión especializada de integración y QA.
- [x] 1.3 Validar especificación estricta y crear rama dedicada.
## 2. Corrección
- [x] 2.1 Cambiar cinco productores a callback_event y validar alias en handler.
- [x] 2.2 Añadir regresión de transporte real, productores y compatibilidad directa.
## 3. Pruebas
- [x] 3.1 Ejecutar suite PedidosYa aislada sin escrituras.
- [x] 3.2 Probar cuatro eventos con HTTPS y RQ reales en desarrollo.
- [x] 3.3 Probar recuperación dirigida 503→204, persistencia y 401.
- [x] 3.4 Cerrar fixtures y comprobar integridad/configuración.
## 4. Cierre
- [x] 4.1 Validar sintaxis, diff, OpenSpec y revisión final.
- [x] 4.2 Documentar resultados/límites y conservar respaldo local recuperable.
- [x] 4.4 Registrar la publicación posteriormente autorizada y su integración; véase la aclaración del 2026-11-13.
- [x] 4.3 Confirmar ausencia de despliegue a producción.

## Evidencia y límites
- 54 pruebas unitarias aprobadas; integración real HTTPS/RQ repetida con éxito.
- Cinco ejecuciones dirigidas de ScheduledJobType; cron global permanece pausado.
- Ensayo de fallo antes del primer commit confirma rollback y limpieza independiente.
- No migraciones, activaciones, merge ni despliegue a producción.
- Límite existente: no renovación automática del token tras 401; jobs antiguos serializados requieren revisión previa al despliegue.

- Revisión final especializada: ambos hallazgos del harness cerrados; sin bloqueos para desarrollo.
- La revisión automática rechazó publicar en el repositorio público por falta de autorización explícita. No se intentó otro mecanismo de publicación.

## Aclaración de vigencia — 2026-11-13

Las restricciones y el rechazo anteriores describen la entrega original. Después
el usuario autorizó expresamente la integración/publicación. La corrección
ba59719 y el merge cc765f9 (renovación del token) pertenecen a la ascendencia del
checkout 8138a20 auditado; la publicación fue confirmada en la conversación de
entrega. No se hizo un push nuevo durante esta actualización documental.

El límite original de no renovar un token tras 401 fue resuelto por el expediente
posterior `refresh-pedidosya-callback-token`, no por este cambio de cola. Su código
y especificación se consultan conjuntamente. Esto no acredita homologación
oficial de PedidosYa ni autoriza nuevas pruebas, scheduler o producción.
