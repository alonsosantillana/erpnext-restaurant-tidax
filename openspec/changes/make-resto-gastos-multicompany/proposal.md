# Propuesta: Resto Gastos multiempresa y por caja

## Problema

`Resto Gastos` registra egresos operativos por fecha, pero no identifica la empresa,
la apertura POS ni el medio de pago. El reporte `Resumen Cierre de Caja` suma todos
los gastos enviados de la fecha, por lo que un gasto puede descontarse del cierre de
otra empresa.

## Objetivo

Separar los gastos por empresa y apertura POS, identificar su medio y cuenta de pago,
usar correlativos independientes por empresa y validar los importes y artículos en el
servidor.

## Alcance

- Añadir compañía, apertura POS, perfil POS, modo de pago y cuenta de pago a
  `Resto Gastos`.
- Configurar una serie de gastos por compañía en `Restaurant Company Settings`.
- Validar coherencia de empresa, apertura, perfil, medio, cuenta y detalles.
- Recalcular el total en el servidor.
- Filtrar los gastos por compañía en `Resumen Cierre de Caja`.
- Añadir filtros y valores derivados en el formulario.

## Exclusiones

- No crear `Journal Entry`, `Payment Entry`, `Purchase Invoice` ni movimientos GL.
- No reclasificar automáticamente gastos históricos que no tienen compañía.
- No cambiar la contabilización ni la integración tributaria de `POS Invoice`.

## Impacto esperado

Cada gasto nuevo pertenecerá inequívocamente a una empresa y una caja abierta. Los
cierres dejarán de mezclar egresos entre compañías y el correlativo será independiente
por abreviatura de compañía.

## Riesgo

Medio. Cambia un DocType submittable y un reporte financiero operativo, pero no crea
asientos contables ni altera comprobantes electrónicos.

## Criterios de aceptación

- Un gasto nuevo requiere compañía, apertura POS, modo y cuenta de pago.
- La apertura, el perfil, el modo y la cuenta pertenecen a la misma compañía.
- Solo se aceptan artículos habilitados del grupo `GASTOS` e importes mayores que cero.
- El total guardado coincide con la suma de sus líneas aunque la petición no provenga
  del formulario web.
- ADDERA y ERPCLOUD generan series distintas y sus cierres solo descuentan sus gastos.
