## Why

El formulario de pago crea un campo vertical por cada medio configurado en el
perfil POS. A medida que aumentan bancos, tarjetas o billeteras, el formulario se
vuelve largo, desplaza el resumen y dificulta operar rapidamente desde caja.

## Objective

Presentar los medios de pago en un selector compacto, similar al selector de
propina, conservando pagos mixtos, teclado numerico y el mismo payload fiscal.

## What Changes

- Reemplazar la lista completa de campos por un selector de medio y un unico
  campo de importe activo.
- Seleccionar inicialmente el medio predeterminado y cargar el saldo pendiente.
- Permitir agregar otros medios para pagos mixtos mediante una lista compacta de
  asignaciones utilizadas.
- Permitir seleccionar, editar y eliminar asignaciones antes de pagar.
- Mostrar pagado, pendiente y cambio mientras se distribuye el cobro.
- Conservar la propina como importe y medio de cobro independiente.
- Mantener la validacion actual: la suma de pagos de la venta debe conciliar con
  el importe fiscal antes de crear la POS Invoice.

## Capabilities

### New Capabilities

- `compact-pos-payment-methods`: Captura compacta y escalable de cobros simples
  y mixtos en el formulario POS del restaurante.

### Modified Capabilities

No existen especificaciones base en `openspec/specs/` que deban modificarse.

## Scope

- App: `restaurant_management`.
- Modulo: formulario cliente `PayForm` de Restaurant Manage.
- Configuracion leida: medios del POS Profile ya cargados en
  `RM.pos_profile.payments`.
- Archivo funcional previsto:
  `restaurant_management/public/restaurant/js/pay-form-class.js`.
- Estilos previstos: hoja CSS de Restaurant Manage o una hoja de pagos existente.
- Pruebas: helpers JavaScript puros y validacion funcional en `v15.local`.

## Exclusions

- No se modifican DocTypes, base de datos, hooks, fixtures ni permisos.
- No se cambia `Table Order.make_invoice`, POS Invoice, impuestos, descuentos,
  series, correlativos ni integracion SUNAT/Nubefact.
- No se cambia la contabilizacion de propinas.
- No se agregan nuevos medios de pago ni se alteran los configurados por empresa.

## Impact

El riesgo es medio porque cambia la interfaz donde se confirma un cobro, pero no
la logica fiscal ni el contrato servidor. La implementacion debe seguir enviando
el mismo objeto `mode_of_payment` con importes positivos y debe ser compatible con
Frappe/ERPNext v15. No agrega dependencias ni requiere `bench migrate`.

Seguridad e integridad:

- solo se muestran medios ya autorizados por el POS Profile de la sesion;
- no se exponen cuentas, credenciales ni datos tributarios adicionales;
- el servidor conserva la validacion definitiva de pagos y totales.

## Acceptance Criteria

- Un perfil con muchos medios muestra un solo selector y un campo de importe, sin
  crecer una fila por medio disponible.
- El medio predeterminado queda seleccionado y recibe inicialmente el saldo total.
- Un pago simple genera el mismo mapa de pago que el formulario actual.
- Se pueden combinar dos o mas medios y la suma se actualiza inmediatamente.
- No pueden coexistir dos asignaciones independientes del mismo medio; seleccionar
  una existente permite editarla.
- Eliminar una asignacion recalcula pagado, pendiente y cambio.
- El teclado numerico opera sobre el importe del medio seleccionado.
- La propina permanece independiente y conserva su propio selector.
- El pago queda bloqueado si la distribucion de la venta no concilia con el total.
