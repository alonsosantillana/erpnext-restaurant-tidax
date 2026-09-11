## 1. Especificación y contrato

- [x] 1.1 Confirmar plataforma React Native/FastAPI, Android piloto y topología inicial.
- [x] 1.2 Consultar Graphify y verificar hallazgos contra código, DocTypes y hooks.
- [x] 1.3 Definir alcance y exclusiones del MVP Resto Tix.
- [x] 1.4 Definir OpenAPI v1 completa, ejemplos y catálogo de errores.
- [x] 1.5 Confirmar el modelo técnico de idempotencia antes de crear metadata.

## 2. Seguridad y contexto

- [ ] 2.1 Implementar autenticación delegada y contexto autorizado.
- [x] 2.2 Validar Company, POS Profile, ambiente y mesa en cada operación.
- [x] 2.3 Añadir límites de entrada, respuestas mínimas y errores estables.
- [ ] 2.4 Probar tokens vencidos/revocados y acceso cruzado.

## 3. Lecturas del MVP

- [x] 3.1 Implementar contexto y capacidades.
- [x] 3.2 Implementar ambientes, mesas y orden activa.
- [x] 3.3 Implementar catálogo paginado con precios/impuestos autoritativos.
- [x] 3.4 Implementar consulta de orden y reconciliación por versión.

## 4. Mutaciones del MVP

- [x] 4.1 Implementar registro idempotente y bloqueo de concurrencia.
- [x] 4.2 Implementar apertura/recuperación de orden.
- [x] 4.3 Implementar alta, cantidad, nota y retiro permitido de líneas.
- [x] 4.4 Implementar envío único de comandas y respuesta autoritativa.
- [x] 4.5 Reutilizar eventos existentes posteriores al commit y reconciliables.

## 5. Validación

- [x] 5.1 Ejecutar pruebas unitarias del nuevo paquete.
- [ ] 5.2 Ejecutar pruebas de doble toque, reintento y concurrencia.
- [ ] 5.3 Comparar catálogo, precios, impuestos y totales con Restaurant Manage.
- [ ] 5.4 Ejecutar regresión de órdenes, cocina, impresión y POS.
- [ ] 5.5 Ejecutar pruebas integradas desde el BFF FastAPI en un sitio aislado.
- [x] 5.6 Registrar comandos, resultados, desviaciones y riesgos residuales.

## 6. Despliegue

- [ ] 6.1 Configurar cliente OAuth y origen HTTPS de QA con autorización explícita.
- [ ] 6.2 Ejecutar `bench migrate` únicamente con autorización explícita.
- [ ] 6.3 Realizar piloto controlado y conservar Restaurant Manage como reversión.
- [ ] 6.4 Confirmar commit, push, revisión y plan de merge.

## Registro de validación

- OpenSpec inicial creado el 2026-09-11.
- Fachada Frappe y OpenAPI v1 implementadas el 2026-09-11.
- Suite aislada: 16 pruebas unitarias exitosas; sin conexión ni escritura a la base de datos.
- Pendientes: autenticación BFF/OAuth integrada, concurrencia real, regresión operativa, migración y despliegue en sitio aislado.
