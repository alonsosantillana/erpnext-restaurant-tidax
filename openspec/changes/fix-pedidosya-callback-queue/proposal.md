## Why
Los cuatro callbacks fallan antes de HTTP: Frappe enqueue reserva event y no lo entrega a send_callback. La recuperación repite el fallo.
## Objective
Restablecer el transporte del evento sin alterar contratos HTTP ni datos operativos.
## Scope
Solo desarrollo, app restaurant_management, service.py, pruebas y documentación. Cambiar los cinco productores a callback_event y conservar event posicional o nombrado en llamadas directas. Sin cambios de DocTypes, hooks, APIs públicas, reportes, fixtures versionadas, migraciones o apps core.
## Exclusions
Producción, despliegues, activación del scheduler general, configuración existente y generación de órdenes operativas. No ampliar políticas de reintento, renovación de tokens o idempotencia.
## Expected Impact
Los callbacks alcanzan el cliente HTTP y el scheduler puede recuperar fallos pendientes. Costo: pruebas locales con receptor existente, sin infraestructura nueva permanente. Riesgo medio por integración externa, acotado a desarrollo y documentos ficticios.
## Acceptance Criteria
Los cuatro eventos llegan correctamente a send_callback mediante enqueue instalado; cinco productores cubiertos; llamadas directas compatibles; argumentos ausentes/inválidos/contradictorios rechazados; HTTP HTTPS y workers RQ reales en cola privada; recuperación programada controlada 503→204, fallos persistentes y 401 sin confirmar notificación. Sin documentos operativos ni cambios de configuración existente.
