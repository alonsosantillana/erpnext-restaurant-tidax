# Especificación: contabilidad de Resto Gastos

## Requisito: contabilización al enviar

Cuando un usuario envía un `Resto Gastos`, el sistema DEBE crear y enviar un
`Journal Entry` balanceado que debite el gasto y acredite la cuenta utilizada
para pagarlo.

### Escenario: producto con cuenta específica

- DADO un producto con `Item Default.expense_account` para la compañía
- CUANDO se envía el gasto
- ENTONCES el asiento usa esa cuenta en el débito.

### Escenario: producto sin cuenta específica

- DADO un producto sin cuenta de gasto por compañía
- Y una cuenta predeterminada configurada en `Restaurant Company Settings`
- CUANDO se envía el gasto
- ENTONCES el asiento usa la cuenta predeterminada.

### Escenario: configuración incompleta

- DADO un producto sin cuenta específica y sin cuenta predeterminada
- CUANDO se guarda o envía el gasto
- ENTONCES el sistema rechaza la operación con un mensaje de configuración.

## Requisito: separación multiempresa

Todas las cuentas y centros de costo DEBEN pertenecer a la compañía del gasto.

## Requisito: cierre íntegro

El sistema NO DEBE permitir enviar un cierre POS si uno de sus gastos enviados
no tiene un `Journal Entry` enviado.

## Requisito: cancelación

Cuando se cancela un gasto antes del cierre, el sistema DEBE cancelar su asiento
vinculado. Las reglas existentes DEBEN seguir impidiendo cancelar el gasto una
vez cerrada la apertura POS.
