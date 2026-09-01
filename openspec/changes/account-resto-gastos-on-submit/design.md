# Diseño

## Momento contable

El asiento se crea durante `on_submit` de `Resto Gastos`. El cierre POS no crea
asientos de gastos: únicamente concilia el saldo esperado y valida la integridad
de los documentos que ya fueron contabilizados.

## Resolución de cuentas

1. `Item Default.expense_account` para el producto y la compañía.
2. `Restaurant Company Settings.default_expense_account` como respaldo.

La cuenta debe estar habilitada, no ser grupo, pertenecer a la compañía y tener
tipo raíz `Expense`. La cuenta de pago debe ser un activo de la misma compañía.
En esta primera versión ambas cuentas deben usar la moneda de la compañía.

## Asiento

- Débito: una línea agrupada por cada cuenta de gasto utilizada.
- Crédito: `Resto Gastos.payment_account` por el total del documento.
- Centro de costo: `Restaurant Company Settings.expense_cost_center`, con
  respaldo en `Company.cost_center`.
- Referencia operativa: enlace `Resto Gastos.journal_entry` y comentario del
  asiento con el gasto y la apertura POS.

## Cancelación e integridad

La cancelación conserva la regla existente que impide cancelar gastos de una
apertura cerrada. Cuando está permitida, cancela el `Journal Entry` vinculado.
Antes de enviar `POS Closing Entry`, todos los gastos enviados de la apertura
deben apuntar a un asiento enviado.
