# Validation

## Baseline

- `get_context` fija `can_pay` en falso.
- `print_order_account` ya comprueba `print` y `write` sobre `Table Order`.
- `Table Order.make_invoice` ya usa `get_restaurant_payment_permissions` y evita pago de órdenes ajenas cuando corresponde.
- `update_item_quantity` rechaza cantidades no enteras, menores a uno o líneas enviadas.
- Graphify actual contiene 2859 nodos y 4326 aristas; fue generado sobre `8601bb5ceae21f2191a57a05e308ff9d53f41abd` y debe regenerarse sobre la implementación final.

## Automated validation (2026-09-14)

- OpenSpec estricto: válido.
- API móvil ERPNext: 22 pruebas unitarias aprobadas.
- Contrato OpenAPI: 11 rutas y referencias internas válidas.
- Compilación Python y `git diff --check`: aprobados.
- Las pruebas simulan impresión y facturación; no generaron documentos financieros reales.

## Pending

- Graphify final: la CLI no está instalada en el servidor; no se instaló por política del proyecto.
- Despliegue coordinado sujeto a aprobación explícita.
