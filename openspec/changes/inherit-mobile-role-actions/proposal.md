## Why

La fachada móvil actual expone lectura y toma de pedidos, pero fija `can_pay` en falso y no permite reutilizar desde Resto TIX las operaciones existentes de pre-cuenta y comprobante. Esto crea una diferencia entre los permisos efectivos del mismo usuario en ERPNext y en la app.

## Objective

Extender la API móvil para publicar capacidades efectivas y ejecutar pre-cuenta y comprobante con las mismas reglas de permiso, propiedad, POS e idempotencia de ERPNext.

## Scope

- Calcular capacidades de impresión y pago desde permisos ERPNext y `get_restaurant_payment_permissions`.
- Exponer opciones mínimas y autorizadas de facturación del perfil POS.
- Envolver la cola existente de pre-cuenta con versión e idempotencia móvil.
- Envolver `Table Order.make_invoice` con validación de orden, cliente, medio de pago y comprobante.
- Mantener `set_quantity` como operación autoritativa para correcciones de cantidad no enviadas.
- Añadir pruebas unitarias y actualizar contrato OpenAPI/Graphify.

## Exclusions

- Modificar roles o permisos configurados.
- Crear clientes, consultar SUNAT, dividir pagos o cobrar propinas desde móvil.
- Alterar platos enviados a producción.
- Ejecutar una factura real durante validación automatizada.

## Risk

**Alto.** El comprobante es una operación financiera. Cada solicitud exigirá autorización sobre la orden, UUID idempotente y versión vigente; el monto se determinará en ERPNext y no se aceptará desde el cliente.

## Acceptance Criteria

- Las capacidades provienen de permisos efectivos y no de nombres de rol codificados en la API móvil.
- Pre-cuenta exige impresión y escritura sobre la orden y reutiliza la cola existente.
- Comprobante exige permiso de pago para el usuario/propietario y un medio configurado en el POS.
- Un UUID repetido devuelve la respuesta previa y no duplica el efecto.
- Las pruebas verifican rutas permitidas y rechazos 403/409 sin efectos reales.
