## Why

ERPNext v15 define series globales fijas para `POS Opening Entry` y
`POS Closing Entry`. En una instalación multiempresa esto mezcla la numeración de
empresas distintas y el formulario no informa qué serie se utilizará.

## Objective

Resolver y mostrar automáticamente la serie de apertura y cierre POS según la empresa
del documento, manteniendo separados sus contadores.

## What Changes

- Agregar series de apertura y cierre POS a `Restaurant Company Settings`.
- Mostrar la serie resuelta como un campo de solo lectura en ambos formularios.
- Generar el nombre mediante hooks de `restaurant_management`, sin modificar ERPNext.
- Validar que Company, POS Profile y apertura vinculada pertenezcan a la misma empresa.
- Migrar las empresas ya configuradas a series basadas en su abreviatura.

## Exclusions

- Renombrar aperturas o cierres históricos.
- Permitir que el cajero seleccione manualmente una serie de otra empresa.
- Compartir contadores entre empresas.

## Acceptance Criteria

- ADDERA y ERPCLOUD generan nombres con prefijos diferentes.
- La serie visible cambia al seleccionar la empresa.
- Una empresa sin configuración recibe un error explícito.
- El backend rechaza combinaciones de empresa, POS Profile o apertura incompatibles.
- Los documentos históricos conservan su nombre.
