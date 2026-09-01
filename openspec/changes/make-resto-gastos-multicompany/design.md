# Diseño

## Modelo

`Resto Gastos` conservará su función de registro operativo. Se añaden enlaces a
`Company`, `POS Opening Entry`, `POS Profile`, `Mode of Payment` y `Account`. El perfil
y la cuenta de pago se derivan de la apertura y del medio de pago para evitar datos
inconsistentes.

`Restaurant Company Settings` incorpora `expense_naming_series`. El valor recomendado
es `GTO-{ABBR}-.YYYY.-.#####` y debe ser único frente a las demás series administradas
por la configuración del restaurante.

## Validaciones

El controlador Python será la fuente autoritativa:

- Compañía obligatoria y accesible para el usuario.
- Apertura enviada, en estado `Open` y de la misma compañía.
- Perfil POS derivado de la apertura.
- Medio de pago presente en la apertura y configurado para el perfil POS.
- Cuenta de pago habilitada, no agrupadora, de tipo activo y de la misma compañía.
- Al menos una línea; artículo habilitado del grupo `GASTOS`; importe positivo.
- Total recalculado desde las líneas con precisión monetaria.

## Interfaz

El formulario toma la compañía predeterminada del usuario, limita las aperturas a las
abiertas de esa compañía y limita los medios de pago a los disponibles en la apertura.
El total continúa actualizándose en pantalla, pero el servidor lo vuelve a calcular.

## Reporte

`Resumen Cierre de Caja` añade `gasto.company = pce.company` en la subconsulta. Los
gastos históricos sin compañía no se asignan automáticamente y quedan fuera del
reporte multiempresa hasta ser regularizados conscientemente.

## Migración y reversión

Un patch completa `expense_naming_series` para cada configuración existente. La
sincronización del DocType agrega las columnas sin modificar documentos históricos.
La reversión del código puede ignorar las columnas nuevas; no se elimina información.

## Permisos y seguridad

Los permisos existentes `resto_cajero` y `resto_admin` se mantienen. El enlace Company
activa el aislamiento estándar mediante permisos de usuario y el controlador valida el
acceso a la compañía al guardar.

## Matriz de pruebas

| Caso | Resultado esperado |
|---|---|
| Gasto ADDERA con apertura ADDERA | Se guarda con serie GTO-ADA y aparece solo en cierre ADDERA |
| Gasto ERPCLOUD con apertura ERPCLOUD | Se guarda con serie GTO-ECS y aparece solo en cierre ERPCLOUD |
| Apertura de otra empresa | Rechazado |
| Apertura cerrada o borrador | Rechazado |
| Medio fuera de la apertura/perfil | Rechazado |
| Cuenta de otra empresa | Rechazado |
| Artículo fuera de GASTOS | Rechazado |
| Importe cero/negativo | Rechazado |
| Total manipulado vía API | Recalculado por el servidor |
| Regresión POS/facturación | Sin cambios en POS Invoice ni SUNAT |
