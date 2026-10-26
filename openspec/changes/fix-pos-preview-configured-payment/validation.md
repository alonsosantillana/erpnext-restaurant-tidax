## Scope and diagnosis

Desarrollo confirmado 192.168.2.53, solo app restaurant_management. Principal
detectada master, inicio b383456 con árbol limpio. Trabajo en rama dedicada
fix/pos-preview-configured-payment. Usuario autorizó tras explicar riesgos del
método compartido. No se accedió al sitio remoto ni a datos operativos locales.

El cash fijo de get_invoice fallaba antes de que make_invoice pudiera sustituirlo
por los pagos reales. Además, set_missing_values nativo refrescaba todos los medios
del perfil cuando la tabla payments estaba vacía. Ahora se siembran los medios
correspondientes antes del refresco y se validan con importes definitivos al final.
Para preview se exige único default habilitado; no se escoge otro arbitrariamente.

Se mantienen validate inicial y final. Revisión del core confirmó que
validate_full_payment no exige pago completo en docstatus 0 aunque _action sea
submit; no se difiere validate ni se cambian fórmulas o descuentos fiscales.

## Files

Modificados:
- restaurant_management/restaurant_management/doctype/table_order/table_order.py
- docs/pedidosya-integration.md

Creados: test_invoice_payments.py junto a Table Order, y proposal.md, design.md,
tasks.md, validation.md y specs/restaurant-pos-preview-payments/spec.md de este
cambio. Ningún archivo eliminado. Sin cambios en otras apps, esquema, hooks,
fixtures, APIs públicas, permisos, precios o configuración.

## Automated results

Desde la raíz de restaurant_management:

```bash
PYTHONDONTWRITEBYTECODE=1 ../../env/bin/python -m unittest \
  restaurant_management.restaurant_management.doctype.table_order.test_invoice_payments -q
PYTHONDONTWRITEBYTECODE=1 ../../env/bin/python -m unittest discover \
  -s restaurant_management/integrations/pedidosya -p 'test_*.py' -q
```

Resultado: 15 pruebas nuevas + 44 existentes aprobadas. DB Mock, conexión real
bloqueada y traducciones simuladas en suite nueva; sin init/connect de sitio ni
bench run-tests (puede borrar Item Price durante inicialización ERPNext).

Cobertura nueva: default válido no cash, default ausente/múltiple/deshabilitado,
perfil de otra empresa/deshabilitado, pagos explícitos/mixtos/vacíos, no persistir
preview, error nativo de cuenta ausente y propagación de error de método inválido.
Recorrido real servicio PedidosYa -> update_item -> aggregate -> get_invoice con
persistencia simulada. set_pos_fields, validate_payment_amount y
validate_full_payment nativos ejecutados en contratos aislados; pago mixto con
descuento se mantiene durante construcción, validación final y submit simulado.

Límites: no se ejecutaron POSInvoice.validate completo ni save/submit reales,
stock, contabilidad, integración HTTP remota, emisión fiscal o proveedor. El error
de método explícito deshabilitado se simula: prueba propagación, no detección
nativa. La validación de cuenta usa get_bank_cash_account real con DB simulada.
La regresión integral en sitio desechable continúa pendiente; no equivale a
certificación PedidosYa ni autorización de uso en producción.

- AST de ambos archivos Python válido, sin generar bytecode.
- git diff --check correcto.
- OpenSpec estricto válido con Node20, antes y después de implementar.
- Revisión especializada de pagos/integración completada, sin bloqueantes.
- Graphify consultado y corroborado contra código; reconstrucción local code-only,
  sin IA externa: 2378 nodos, 4363 relaciones finales y 259 comunidades. graphify-out ignorado
  por Git, no versionado. Sin instalar hooks ni cambiar configuración de agentes.

## Handoff and pending operation

No se ejecutaron migrate, build, clear-cache, restart, patches ni modificaciones de
datos/configuración. No hace falta migración o build por este cambio Python.

Implementación revisada en rama de trabajo. El usuario autorizó posteriormente:
«ok pasa los cambios a la rama principal y push remoto». Se repitieron las 59
pruebas aisladas y se validó OpenSpec antes de preparar el commit, su integración
en master y publicación en upstream (alonsosantillana/erpnext-restaurant-tidax).
Esta autorización de publicación no incluye despliegue ni cambios de sitios.

Una vez desplegado en el entorno de pruebas por el usuario, revisar el estado de
PYA-2026-00003. Si sigue Error sin Table Order, usar Retry Processing del mismo
registro, no crear token nuevo. Direct sin autoaccept debe terminar Awaiting
Acceptance con una única orden/fulfillment, sin aceptar/cobrar/emitir. Scheduler
puede haber reintentado antes: comprobar enlaces primero. Si falla por otra
configuración, revisar el error preciso sin habilitar cash ni cambiar precios.

Regresión manual pendiente: mesa, pickup, delivery y cobro mixto/descuentos en
sitio desechable con cuentas y apertura reales, verificando importes y asientos.
Rollback: revertir únicamente el futuro commit de esta rama; sin esquema o datos
que restaurar. Refrescar procesos solo dentro de despliegue autorizado.
