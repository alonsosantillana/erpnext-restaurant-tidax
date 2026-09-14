## Permission Model

`get_context` reutiliza `frappe.has_permission` para órdenes y `get_restaurant_payment_permissions` para pago. La capacidad de pre-cuenta requiere `print` y `write` en `Table Order`. La capacidad de comprobante usa el permiso POS existente, incluidos los campos configurables del usuario en el perfil POS.

Las capacidades son una ayuda de presentación. `print_pre_account`, `get_billing_options` y `create_invoice` vuelven a validar la orden concreta con `_validate_order_access` y las funciones existentes.

## Pre-account Adapter

La fachada acepta UUID y versión, bloquea la orden, valida ámbito y llama `restaurant_management.api.print_order_account`. El mismo UUID se usa en el registro móvil y como `request_id` de la cola, evitando duplicados por reintentos.

## Billing Adapter

Las opciones se obtienen del POS Profile asignado al usuario. Solo se exponen cliente predeterminado, medios de pago habilitados y combinaciones de comprobante soportadas por `VOUCHER_CONFIG`.

La creación de comprobante no recibe monto del cliente. Después de validar permiso, versión, cliente y medio POS, llama `Table Order.make_invoice` con el total calculado por la orden. La respuesta conserva el identificador de factura y estado de emisión electrónica, sin exponer documentos no autorizados.

## Idempotency and Concurrency

Las dos mutaciones usan `Restaurant Mobile Request`. El hash canónico incluye parámetros comerciales y versión. Una solicitud completada se devuelve desde caché; una versión obsoleta produce 409 antes del efecto.

## Rollback

Retirar los métodos nuevos y restaurar `get_context`. No hay migraciones. Impresiones o comprobantes ya confirmados no se revierten automáticamente.
