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
- [ ] 4.4 Publicar rama en GitHub: pendiente autorización explícita por repositorio público.
- [x] 4.3 Confirmar ausencia de despliegue a producción.

## Evidencia y límites
- 54 pruebas unitarias aprobadas; integración real HTTPS/RQ repetida con éxito.
- Cinco ejecuciones dirigidas de ScheduledJobType; cron global permanece pausado.
- Ensayo de fallo antes del primer commit confirma rollback y limpieza independiente.
- No migraciones, activaciones, merge ni despliegue a producción.
- Límite existente: no renovación automática del token tras 401; jobs antiguos serializados requieren revisión previa al despliegue.

- Revisión final especializada: ambos hallazgos del harness cerrados; sin bloqueos para desarrollo.
- La revisión automática rechazó publicar en el repositorio público por falta de autorización explícita. No se intentó otro mecanismo de publicación.
