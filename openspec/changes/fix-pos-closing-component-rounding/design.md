## Context

La consolidación de ERPNext mapea los importes netos de cada línea y conserva los
impuestos de cada Factura POS. Ambos se almacenan con precisión monetaria. La suma de
muchos componentes redondeados puede diferir del total redondeado del comprobante.

## Decisions

### Tolerancia limitada por componentes

Para `N` componentes monetarios no nulos (líneas más impuestos), el máximo residual
aceptable será `ceil(N / 2)` unidades de la precisión de moneda, con un mínimo de una
unidad. Este límite representa el peor caso agregado de redondear componentes a la
precisión monetaria y evita usar un importe fijo arbitrario.

### Aislamiento por Factura POS

Cada residual se calcula y asigna solamente a una línea elegible proveniente de la
misma Factura POS. No se compensan diferencias entre comprobantes distintos.

### Impuestos y documento de origen

Los impuestos y la Factura POS emitida no se modifican. El residual se aplica al
importe neto de una línea del documento consolidado, actualizando importe, tasa y sus
valores base relacionados.

### Moneda base y devoluciones

El residual de moneda y el residual base se validan contra sus tolerancias respectivas
y se aplican independientemente. En devoluciones se selecciona una línea negativa y el
ajuste nunca cambia su signo.

## Risks

- Una tolerancia demasiado amplia podría ocultar datos corruptos. La fórmula queda
  limitada por el número real de componentes no nulos y conserva el bloqueo superior.
- La línea elegida puede tener cantidad mayor que uno; se mantiene precisión interna
  en la tasa para conservar exactamente el importe ajustado.

## Rollback

Revertir la función de tolerancia restaura el límite fijo de una unidad monetaria. No
se requiere reversión de datos porque la Factura POS original no se modifica.
