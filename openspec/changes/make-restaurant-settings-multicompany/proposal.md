## Why

`Restaurant Settings` es un DocType `Single`, por lo que todas las empresas del sitio
comparten restricciones, canales externos, formatos de impresión y series tributarias.
Aunque `Table Order` y `Restaurant Fulfillment` ya guardan `company`, los ambientes,
mesas y centros de producción tampoco tienen empresa y pueden mezclarse entre sesiones.

## Objective

Resolver la configuración y los objetos operativos del restaurante por empresa, sin
perder la configuración existente ni cambiar pedidos o comprobantes históricos.

## What Changes

- Crear `Restaurant Company Settings`, con un registro único por `Company`.
- Centralizar la resolución de configuración usando la empresa de la orden,
  fulfillment, POS Profile o empresa activa del usuario.
- Mantener `Restaurant Settings` como fallback legado temporal de solo compatibilidad.
- Migrar de forma idempotente los valores legados a la empresa predeterminada.
- Agregar `company` a `Restaurant Object` y hacer que mesas y centros hereden la
  empresa de su ambiente.
- Filtrar ambientes, objetos, contadores, producción y permisos por empresa.
- Validar que POS Profile, orden, mesa, fulfillment y configuración pertenezcan a la
  misma empresa.

## Scope

- DocTypes `Restaurant Settings`, `Restaurant Company Settings`, `Restaurant Object`,
  `Table Order` y `Restaurant Fulfillment`.
- Página `Restaurant Manage`, Production Center, facturación POS, delivery/recojo,
  precuenta, restricciones y eventos realtime.
- Patch de migración, pruebas unitarias y regresión funcional v15.

## Exclusions

- Separar impresoras físicas de `silent_print` por empresa; el enrutamiento físico
  continuará perteneciendo a Work Station/Production Center.
- Reescribir permisos de usuario de ERPNext.
- Modificar reglas SUNAT o series de documentos ya emitidos.
- Replicar automáticamente las mismas series fiscales a todas las empresas.

## Risk

**Alto** para aislamiento y facturación: una resolución incorrecta podría usar series,
formatos o datos de otra empresa. La migración no elimina el `Single` anterior y puede
revertirse conservando los registros nuevos.

## Acceptance Criteria

- Cada empresa puede guardar una configuración diferente.
- Una orden usa siempre la configuración correspondiente a `Table Order.company`.
- Delivery/recojo consulta la empresa y POS Profile activos.
- Los ambientes, mesas y centros visibles pertenecen únicamente a la empresa activa.
- No se permite transferir una orden a una mesa de otra empresa.
- Production Center no muestra ni cambia platos de otra empresa.
- La empresa predeterminada conserva los valores actuales tras la migración.
- Una empresa sin configuración recibe un error explícito; no reutiliza silenciosamente
  las series de otra empresa.
- Dos sesiones en empresas distintas no comparten salas, contadores, comandas, series
  ni eventos funcionales.
