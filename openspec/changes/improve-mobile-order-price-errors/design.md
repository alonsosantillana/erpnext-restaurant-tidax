## Architecture

La fachada móvil seguirá obteniendo el catálogo desde `get_restaurant_items`, usando la lista de precios configurada por el `POS Profile`. Antes de construir la entrada para `TableOrder.push_item`, verificará que la tasa resuelta sea mayor que cero.

## Affected Components

- App: `restaurant_management`.
- API: `restaurant_management.mobile_api.v1`.
- Dominio reutilizado: `TableOrder`; sin modificaciones.
- DocTypes consultados: `POS Profile`, `Item` e `Item Price` a través del flujo existente.
- Hooks, fixtures, patches, reportes y metadata: sin cambios.

## Error Contract

El error estable será:

```text
ITEM_PRICE_MISSING
HTTP 409
The requested item has no price configured in the POS price list
```

Se usa 409 porque el producto existe y está autorizado, pero su configuración comercial vigente impide completar la operación.

## Send Command Regression

`TableOrder.send` está decorado con `@property`. Por ello, `send_command` debe evaluarlo como `order.send`; convertirlo en `order.send()` mutaría la orden y luego intentaría invocar el diccionario retornado. Se conservará la implementación y se añadirá una prueba para evitar una regresión.

## Permissions and Transactions

No cambian permisos, bloqueos, idempotencia ni límites transaccionales. La validación ocurre antes de `order.push_item`, dentro de la transacción actual, y no añade commits manuales.

## Test Matrix

| Caso | Resultado esperado |
|---|---|
| Precio positivo | Entrada con `rate` y `price_list_rate` autoritativos |
| Precio ausente o cero | `ITEM_PRICE_MISSING`, HTTP 409, sin mutación |
| Envío con líneas pendientes | La propiedad `send` se evalúa exactamente una vez |
| Prueba QA reversible | Alta temporal exitosa y rollback confirmado |

## Rollback

Restaurar `restaurant_management/mobile_api/v1.py` y `restaurant_management/mobile_api/test_v1.py` desde el punto anterior de la rama. No requiere migración, reversión de datos ni reinicio de infraestructura.

## Risks and Mitigations

- **Precio promocional igual a cero:** el dominio actual ya rechaza tasas no positivas; la fachada mantiene esa política.
- **Mensaje no localizado en el BFF:** el código estable permite mapearlo sin exponer una traza interna.
- **Confusión con `send`:** prueba explícita de la propiedad y verificación directa del código fuente.
