## Architecture

Graphify identifica get_invoice como dependencia de update_item, aggregate,
calculate_order y make_invoice; las llamadas se corroboraron en código. El helper
mantiene los cálculos fiscales y validate de ERPNext, sin omitir validaciones.

Un helper local resuelve el único default de POS Profile.payments para previsualizar.
Comprueba empresa, perfil habilitado y Mode of Payment.enabled. No hay fallback
global ni al primer medio arbitrario. ERPNext sigue resolviendo y validando las
cuentas de cada medio para la empresa; errores de cuenta no se silencian.

get_invoice conserva entry_items/make y agrega mode_of_payment opcional. None
requiere el default temporal por grand_total; un mapping explícito conserva cada
importe, y {} se rechaza. make_invoice pasa el mapping real y no lo reemplaza tras
la primera validación. Los pagos se siembran antes de set_missing_values (default
temporal con importe 0) para evitar que ERPNext cargue todos los medios del perfil,
incluidos otros deshabilitados o sin cuenta. Después del cálculo se restaura el
mapping explícito o se asigna grand_total al default; las cuentas de los métodos
usados siguen bajo validación nativa. No se amplían permisos ni agregan restricciones nuevas de
pertenencia al perfil a pagos explícitos. El default temporal no significa recepción
de dinero ni genera GL, Payment Entry, Journal Entry o comprobante persistido.

## Components and risks

- Modificado: restaurant_management/restaurant_management/doctype/table_order/table_order.py.
- Nuevo: pruebas unitarias aisladas de pagos de factura temporal.
- Sin cambios en integraciones.pedidosya, APIs, hooks, reportes, fixtures o esquema.
- set_missing_values nativo sigue cargando configuración POS; no se altera su
  código. La lista de pagos elegida evita el refresco nativo de medios ajenos.
  Errores de cuentas de los métodos usados no se omiten.
- Riesgo: afectar pagos reales. Mitigación: probar mapping explícito/mixto, vacío,
  orden de validación, defaults inválidos y fallo nativo, sin persistencia real.

## Validation and rollout

Pruebas unittest con DB simulada, conexión bloqueada y sin iniciar sitio. Regresión
PedidosYa aislada. Sintaxis AST, diff --check, OpenSpec estricto Node20 y revisión
especializada. No ejecutar bench run-tests sobre un sitio operativo (riesgo de
borrar Item Price). Regresión integral en sitio desechable queda pendiente.

Tras publicación/despliegue autorizado, reintentar PYA existente mediante Retry
Processing; no cambiar token ni crear otro pedido. Esperado Direct sin autoaccept:
Awaiting Acceptance, con una orden y fulfillment, sin cobrar/emitir/aceptar. Confirmar
por separado mesa, pickup, delivery y cobro mixto antes de uso general.

## Rollback

Rama fix/pos-preview-configured-payment basada en master. Revertir únicamente el
commit de esta corrección y refrescar procesos solo con autorización. Sin migración
inversa, datos o precios que restaurar. Conservar inbox y documentos para auditoría.
