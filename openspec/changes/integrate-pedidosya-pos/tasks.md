## 1. Especificacion y baseline

- [x] 1.1 Revisar documentacion oficial, delivery actual, Graphify y riesgos.
- [x] 1.2 Definir limites de la primera fase y criterios de aceptacion.
- [x] 1.3 Validar OpenSpec en modo estricto con Node.js 20.

## 2. Modelo y configuracion

- [x] 2.1 Crear configuracion de sucursal con credenciales cifradas y validaciones.
- [x] 2.2 Crear tabla de mapeo remoto a Item.
- [x] 2.3 Crear inbox/outbox idempotente de pedidos con payload cifrado.
- [x] 2.4 Adaptar fulfillment para delivery de plataforma sin Address obligatorio.

## 3. Receptor y procesamiento

- [x] 3.1 Implementar validacion JWT y endpoint de dispatch.
- [x] 3.2 Persistir y reconocer reintentos con el mismo `remoteOrderId`.
- [x] 3.3 Procesar asincronamente cliente, productos, precios, orden y fulfillment.
- [x] 3.4 Evitar produccion para test orders y ordenes invalidas.
- [x] 3.5 Recuperar eventos pendientes/fallidos mediante tarea programada.

## 4. Estados salientes y entrantes

- [x] 4.1 Obtener/cachear token y validar callback URLs.
- [x] 4.2 Aceptar/rechazar y notificar pedido preparado.
- [x] 4.3 Recibir cancelacion y estados extensibles de forma idempotente.
- [x] 4.4 Conectar Ready con callback externo sin bloquear cocina.

## 5. Seguridad y pruebas

- [x] 5.1 Probar autenticacion, secreto, URL allowlist y minimizacion de errores.
- [x] 5.2 Probar idempotencia, mapeos, test orders y fallos atomicos.
- [x] 5.3 Probar contratos de callbacks; HTTP real queda para staging.
- [ ] 5.4 Ejecutar regresion relevante de delivery/Table Order en un sitio desechable.
- [x] 5.5 Validar Python, JSON, OpenSpec y revisar diff.

## 6. Operacion y cierre

- [x] 6.1 Documentar configuracion, URL publica, onboarding y rollback.
- [x] 6.2 Regenerar Graphify local sin versionar artefactos generados.
- [x] 6.3 Registrar validaciones y desviaciones.
