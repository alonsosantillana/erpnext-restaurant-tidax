# Especificación: contabilidad de Resto Gastos

## ADDED Requirements

### Requirement: Expense accounting on submission

Cuando un usuario envía un `Resto Gastos`, el sistema SHALL crear y enviar un
`Journal Entry` balanceado que debite el gasto y acredite la cuenta utilizada
para pagarlo.

#### Scenario: Product with company-specific expense account

- DADO un producto con `Item Default.expense_account` para la compañía
- CUANDO se envía el gasto
- ENTONCES el asiento usa esa cuenta en el débito.

#### Scenario: Product without company-specific expense account

- DADO un producto sin cuenta de gasto por compañía
- Y una cuenta predeterminada configurada en `Restaurant Company Settings`
- CUANDO se envía el gasto
- ENTONCES el asiento usa la cuenta predeterminada.

#### Scenario: Incomplete accounting configuration

- DADO un producto sin cuenta específica y sin cuenta predeterminada
- CUANDO se guarda o envía el gasto
- ENTONCES el sistema rechaza la operación con un mensaje de configuración.

### Requirement: Company isolation

Todas las cuentas y centros de costo SHALL pertenecer a la compañía del gasto.

#### Scenario: Cross-company account or cost center

- **WHEN** una cuenta o centro de costo pertenece a otra compañía
- **THEN** la validación SHALL rechazar el gasto antes de contabilizarlo

### Requirement: Expense accounting integrity before POS closing

El sistema SHALL NOT permitir enviar un cierre POS si uno de sus gastos enviados
no tiene un `Journal Entry` enviado.

#### Scenario: Submitted expense without submitted accounting entry

- **WHEN** se intenta enviar el cierre de una apertura con un gasto enviado sin asiento vigente
- **THEN** el cierre SHALL quedar bloqueado con un mensaje de integridad contable

### Requirement: Coordinated expense cancellation

Cuando se cancela un gasto antes del cierre, el sistema SHALL cancelar su asiento
vinculado. Las reglas existentes SHALL seguir impidiendo cancelar el gasto una
vez cerrada la apertura POS.

#### Scenario: Cancellation before closing

- **WHEN** se cancela un gasto cuya apertura sigue abierta y no tiene cierre enviado
- **THEN** su asiento enviado SHALL cancelarse junto con el gasto

#### Scenario: Cancellation after closing

- **WHEN** el gasto pertenece a una apertura cerrada o incluida en un cierre enviado
- **THEN** el controlador SHALL rechazar la cancelación del gasto
