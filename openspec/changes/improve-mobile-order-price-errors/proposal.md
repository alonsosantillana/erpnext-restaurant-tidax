## Why

Resto Tix devolvía un error genérico del BFF al agregar un producto sin precio vigente en la lista de precios del POS. ERPNext rechazaba correctamente la operación, pero la fachada móvil no emitía un código de error estable que permitiera explicar la causa al usuario.

## Objective

Validar el precio autoritativo antes de mutar una orden y devolver un error estable cuando el producto no tenga un precio positivo en la lista configurada por el POS Profile.

## Scope

- Validación de precio en `restaurant_management.mobile_api.v1._new_item_entry`.
- Prueba unitaria del error `ITEM_PRICE_MISSING`.
- Prueba de regresión que confirme la semántica vigente de `TableOrder.send` como propiedad.
- Validación transaccional y reversible del alta de un plato con precio vigente.

## Exclusions

- Crear o modificar precios, listas de precios o POS Profiles.
- Cambiar impuestos, descuentos, inventario, facturación o producción.
- Cambiar la implementación de `TableOrder.send`.
- Modificar el BFF o la aplicación móvil.

## Expected Impact

- Los productos con precio vigente continúan agregándose mediante las reglas actuales de ERPNext.
- Los productos sin precio producen un error identificable y no alcanzan la mutación de la orden.
- No se requiere migración ni cambio de datos.

## Risk

**Medio-bajo.** Se añade una validación previa en una API de mutación. La regla coincide con la validación ya aplicada posteriormente por el dominio de `TableOrder`.

## Acceptance Criteria

- Un precio positivo crea la entrada móvil con precio y tasa autoritativos.
- Un precio ausente, cero o negativo genera `ITEM_PRICE_MISSING` con HTTP 409.
- La suite de `restaurant_management.mobile_api.test_v1` queda verde.
- Una prueba transaccional sobre QA agrega temporalmente un producto con precio y revierte el cambio.
- No se modifica ni persiste ningún pedido durante las pruebas automáticas o diagnósticas.
