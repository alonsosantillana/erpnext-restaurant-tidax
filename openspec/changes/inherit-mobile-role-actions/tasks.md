## 1. Contract

- [x] 1.1 Consultar Graphify y código existente de permisos, pre-cuenta, pago y cantidades.
- [x] 1.2 Definir capacidades, idempotencia, validación de versión y exclusiones.
- [x] 1.3 Actualizar OpenAPI móvil.

## 2. Implementation

- [x] 2.1 Calcular capacidades efectivas en `get_context`.
- [x] 2.2 Añadir opciones autorizadas de facturación.
- [x] 2.3 Añadir pre-cuenta idempotente y versionada.
- [x] 2.4 Añadir creación idempotente y versionada de comprobante.
- [x] 2.5 Añadir pruebas unitarias sin impresión ni comprobante reales.

## 3. Validation

- [x] 3.1 Ejecutar pruebas de API móvil y regresión relevante.
- [x] 3.2 Validar OpenSpec estricto y contrato OpenAPI.
- [ ] 3.3 Regenerar Graphify sin LLM y registrar resultados.
- [x] 3.4 Revisar diff y estado Git.

## 4. Delivery

- [ ] 4.1 Coordinar despliegue de ERPNext antes del BFF/APK.
- [ ] 4.2 Solicitar aprobación antes de commit, push, migrate o restart.
