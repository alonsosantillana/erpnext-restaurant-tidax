# Propuesta: contabilizar Resto Gastos al enviarlo

## Problema

`Resto Gastos` reduce el efectivo esperado del cierre POS, pero actualmente no
genera un movimiento en el Libro Mayor. Esto deja una diferencia entre el
control operativo de caja y la contabilidad.

## Solución

- Resolver una cuenta de gasto por producto y empresa desde `Item Default`.
- Usar una cuenta de gasto predeterminada en `Restaurant Company Settings`
  cuando el producto no tenga una cuenta específica.
- Crear y enviar un `Journal Entry` al enviar cada `Resto Gastos`.
- Debitar las cuentas de gasto y acreditar la cuenta del método de pago.
- Cancelar el asiento cuando se cancele el gasto antes del cierre.
- Impedir el cierre si existe un gasto enviado sin asiento contable vigente.

## Fuera de alcance

- Crédito fiscal, impuestos y comprobantes de proveedor.
- Creación automática de `Purchase Invoice` o `Payment Entry`.
- Contabilización retroactiva de gastos pertenecientes a aperturas ya cerradas.
