# Compatibilidad de restaurant_management con Frappe/ERPNext v16

## Why
El upgrade autorizado de desarrollo requiere resolver APIs removidas sin perder las restricciones y contratos existentes.

## What Changes
- import desktop y adaptador de consulta POS legado/v16.
- Preservar lista legada de POS Invoice y payload v16 invoices/payments/taxes. No modificar calculos ni escrituras contables.
- Pruebas puras y chequeo de sintaxis; sin llamadas externas.

## Impact
Riesgo alto por interfaces de permisos/POS; el alcance es un adaptador de compatibilidad sin nuevas reglas de negocio. Autorizacion: usuario solicito proceder con el upgrade el 2026-11-01 y coordinador asigno estas correcciones.
No se modifican DocTypes, fixtures, impuestos, series, calculos, datos ni servicios.

## Acceptance
Imports compatibles; contratos/denegaciones existentes preservados; pruebas puras aprobadas; commit/push verificables. UAT transaccional permanece pendiente.
