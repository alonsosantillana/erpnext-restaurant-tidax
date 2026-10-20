## 1. Reconciliación

- [x] 1.1 Calcular tolerancia proporcional a líneas e impuestos no nulos.
- [x] 1.2 Validar por separado importe del documento e importe base.
- [x] 1.3 Mantener el ajuste dentro de la Factura POS y conservar signos.

## 2. Pruebas

- [x] 2.1 Cubrir diferencia acumulada de S/ 0.03 con once líneas.
- [x] 2.2 Cubrir diferencias por encima del límite calculado.
- [x] 2.3 Cubrir devoluciones y moneda base independiente.
- [x] 2.4 Validar contra `BV-BRE2-000022` sin persistir cambios.

## 3. Validación

- [x] 3.1 Ejecutar pruebas focalizadas y verificaciones estáticas.
- [x] 3.2 Actualizar Graphify y validar OpenSpec con Node.js 20.
- [ ] 3.3 Reintentar el cierre y comprobar la Factura de Venta consolidada.
