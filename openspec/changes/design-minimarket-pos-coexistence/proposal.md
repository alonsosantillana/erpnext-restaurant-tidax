# Disenar convivencia POS de restaurante y minimarket

## Why

La nueva operacion de minimarket utilizara una Company independiente dentro del
sitio de desarrollo compartido. La separacion por empresa no desactiva hooks,
scripts cliente ni POS Settings globales de restaurant_management/ERPNext.
Se necesita un expediente revisable antes de modificar estos procesos criticos.

## What Changes

- Documentar contratos reales, dominios por empresa/perfil y ventanas incompletas.
- Especificar guardas futuras de series, gastos, cierre y scripts cliente.
- Conservar modalidad POS global sin seleccion ficticia por Company/POS Profile.
- Definir regresion nativa y restaurante, seguridad, flags y reversion.
- Enlazar la futura implementacion a su propio alcance aprobado por repositorio.

## Capabilities

### New Capabilities

- `restaurant-pos-coexistence-design`: contrato documental de convivencia y pruebas.

### Modified Capabilities

Ninguna en esta entrega: no se cambia comportamiento ni se consolidan requisitos
funcionales implementados. La implementacion posterior debera revisar los deltas
que correspondan a series, gastos, cierre y compatibilidad POS existentes.

## Impact

Solo este expediente Markdown, sobre version-16 desde c96d967. Riesgo bajo de la
entrega documental; riesgo alto de una futura implementacion por ventas, caja,
stock y contabilidad. No cambia core, hooks, Python/JS, DocTypes, permisos,
fixtures, patches, configuracion, datos, sesiones o integraciones.

Dependencia de diseno: minimarket_management, cambio design-minimarket-operation.
Su navegacion se implementa en expediente separado; no habilita cobrar ni abrir
sesiones automaticamente. No se requiere dependencia Python entre ambas apps.

## Acceptance and exclusions

Fuentes/Graphify revisados, limites explicitos y escenarios trazables; validacion
estricta de este cambio y diff sin errores. Pruebas funcionales, nuevos perfiles,
ventas, emision, impresion, migracion y activacion quedan pendientes y requieren
el alcance/entorno autorizado de su futura implementacion. No ejecutar hooks ni
pruebas con datos como parte de este diseno.
