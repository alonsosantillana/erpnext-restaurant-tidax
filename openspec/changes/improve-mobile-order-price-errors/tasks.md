## 1. Análisis y especificación

- [x] 1.1 Confirmar el error real y la lista de precios del POS.
- [x] 1.2 Consultar Graphify y verificar las relaciones contra el código.
- [x] 1.3 Confirmar que `TableOrder.send` es una propiedad y no un método invocable.
- [x] 1.4 Documentar alcance, riesgos y reversión.

## 2. Implementación

- [x] 2.1 Añadir el error estable `ITEM_PRICE_MISSING` antes de mutar la orden.
- [x] 2.2 Añadir cobertura unitaria del precio faltante.
- [x] 2.3 Añadir cobertura de regresión para la evaluación única de `TableOrder.send`.

## 3. Validación

- [x] 3.1 Compilar los archivos Python afectados.
- [x] 3.2 Ejecutar la suite aislada de la fachada móvil.
- [x] 3.3 Validar OpenSpec en modo estricto disponible.
- [x] 3.4 Ejecutar una prueba transaccional de alta con precio vigente y confirmar rollback.
- [x] 3.5 Confirmar la prueba real desde el BFF y el celular.

## 4. Entrega

- [x] 4.1 Revisar estado Git y diff sin credenciales ni artefactos temporales.
- [x] 4.2 Ejecutar commit, integración a la rama principal y push con autorización del usuario.
