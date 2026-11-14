# Base consolidada de requisitos

Actualización documental: 2026-11-13 (America/Lima). Fuente ejecutable revisada:
`8138a20`; esta publicación documental se adapta a la base de mantenimiento
`037c8a1`. La base consolidada de version-16 conserva siete capacidades existentes,
no introduce funcionalidad ni certifica despliegue o aceptación transaccional.

## Capacidades revisadas

| Capacidad | Expediente de origen | Evidencia o fuente |
| --- | --- | --- |
| resto-gastos-multicompany | make-resto-gastos-multicompany | Controlador RestoGastos, series, reporte y evidencia histórica |
| resto-gastos-accounting | account-resto-gastos-on-submit | expense_accounting.py, hooks.py y validación histórica |
| desk-printer-indicator | fix-v16-printer-indicator | Indicador, fixtures históricos y confirmación acotada del operador |
| restaurant-permission-compatibility | fix-v16-print-permission-api | Guards de impresión/electrónica y evidencia propia |
| v16-compatibility | migration-v16-compatibility | Adaptadores existentes y pruebas aisladas documentadas |
| pedidosya-callback-queue | fix-pedidosya-callback-queue | Productores/handler de callbacks y verificación HTTPS/RQ histórica |
| pedidosya-callback-auth | refresh-pedidosya-callback-token | Cliente con renovación 401 acotada y aislamiento del token |

Los requisitos se conservan en el expediente original y se presentan aquí como
base de consulta. Los deltas `ADDED` son exclusivos de `changes/`; la base no los
repite. Ningún expediente se archiva automáticamente por pasar validación.

## Cobertura y límites

No se declara consolidación exhaustiva de las demás capacidades. Los expedientes
de `../changes/` siguen siendo la fuente de sus decisiones, escenarios y pendientes.
Las casillas incompletas se mantienen, salvo hechos concretos verificados durante
esta actualización. Los documentos históricos v15 se conservan como tales; el
trabajo actual corresponde exclusivamente a v16.

En particular, la antigua exclusión de contabilidad en gastos multiempresa fue
ampliada por el expediente contable posterior: hoy se leen ambas capacidades en
conjunto. La cotización nativa de carrito de la revisión auditada no se incorpora
a esta base consolidada de mantenimiento: su código y expediente permanecen en
la rama candidata. Su integración, activación en TIX y homologación requieren
autorización separada. La consolidación original de ocho capacidades se conserva
en el commit documental ccdf75a, sin fusionar sus ancestros funcionales.

Estado, comprobaciones y pendientes: [mantenimiento del conocimiento](../../docs/project-knowledge.md).
