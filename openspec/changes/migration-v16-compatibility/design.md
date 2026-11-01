# Diseno

## Contexto y alcance
App restaurant_management, rama dedicada desde el checkout activo para conservar sus commits. Otras apps y core fuera de esta correccion.
APIs afectadas: import desktop y adaptador de consulta POS legado/v16.

## Decisiones
Preservar lista legada de POS Invoice y payload v16 invoices/payments/taxes. No modificar calculos ni escrituras contables.
Se usan wrappers de firmas nuevas que delegan los controles nativos y preservan filtros existentes. Un retorno neutro None del hook has_permission pasa a True donde corresponda; las denegaciones False no cambian.

## Datos y migracion
No aplica cambio de esquema ni patch. No se ejecutan escrituras, migracion ni integraciones desde las pruebas. La migracion del sitio es responsabilidad del coordinador.

## Pruebas
Sintaxis y escenarios puros con dobles: contratos JSON/POS, filtrado de resultados, propagacion de argumentos v16 y rechazo de acceso fuera de alcance. No equivalen a UAT ni validacion contable.

## Reversion
Volver al branch/commit de origen registrado antes de los cambios, con checkout limpio. No hay datos creados por este ajuste. No eliminar ramas ni restablecer base de datos.

## Dependencias
Frappe/ERPNext v16 y runtime son preparados por el coordinador. No se actualiza infraestructura desde esta tarea.

## Revision especializada y contratos
Se conserva triestado en helpers compartidos de descarga; solo el hook de Frappe devuelve boolean. Se comprobaron APIs, campos de tabla POS v15/v16 y modo de factura. Los selectores de parentfield SQL usan parametros fijos segun version, sin cambiar consultas agregadas ni reglas contables.
