## 1. Especificación

- [x] 1.1 Documentar el límite transaccional, la idempotencia y la recuperación.
- [x] 1.2 Limitar la recuperación automática a comprobantes marcados por Restaurant Manage.

## 2. Implementación

- [x] 2.1 Agregar estado, intentos, fecha y error sanitizado a POS Invoice.
- [x] 2.2 Encolar la sincronización después del commit.
- [x] 2.3 Consultar antes de generar bajo un lock por comprobante.
- [x] 2.4 Recuperar estados reintentables y envíos abandonados mediante scheduler.
- [x] 2.5 Liberar la interfaz y consultar el estado sin bloquear el POS.

## 3. Validación

- [x] 3.1 Ejecutar pruebas unitarias del encolado, aceptación, timeout e idempotencia.
- [x] 3.2 Validar OpenSpec y sintaxis JavaScript/Python.
- [x] 3.3 Recuperar y verificar BV-BRE2-000017 mediante consulta previa.
