# Requisitos: gastos en cierre POS

## Conciliación

### Requisito: cálculo neto por método de pago

El sistema DEBE calcular el saldo esperado de cada método como fondo inicial más ventas
cobradas menos gastos enviados de la misma apertura y método de pago.

#### Escenario: gasto en efectivo

- DADO un fondo de S/ 100, ventas por S/ 500 y gastos por S/ 80 en efectivo
- CUANDO se prepara el cierre
- ENTONCES el esperado DEBE ser S/ 520
- Y el total vendido DEBE permanecer en S/ 500

### Requisito: aislamiento

El sistema DEBE excluir gastos de otra apertura, empresa o método de pago.

### Requisito: borradores

El sistema NO DEBE permitir enviar el cierre cuando existen gastos en borrador asociados
a su apertura.

### Requisito: integridad histórica

El sistema NO DEBE permitir cancelar un gasto enviado que ya forma parte de un cierre
POS enviado.

### Requisito: idempotencia

Guardar o refrescar repetidamente el cierre NO DEBE descontar un gasto más de una vez.
