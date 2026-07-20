# Evidencia de calificación v15

Fecha: 2026-07-20
Sitio autorizado: v15.local

## Resultado del bloque de runtime

| Verificación | Resultado |
|---|---|
| Instalar silent_print 0.0.1 | Correcto |
| Instalar restaurant_management 1.7.7 en Frappe/ERPNext 15.109.0 | Correcto |
| Sincronizar Desk Form y Desk Form Field | Correcto |
| Importar los 11 Desk Forms estándar | Correcto |
| Cargar payment-order mediante la API protegida | Correcto |
| Sincronizar RM Producto a Producir Detalle | Correcto |
| Build de assets helper | Correcto |
| Asset jshtml-class.js por HTTP | 200 OK |
| Ruta /app/restaurant-manage como Guest | Redirección a login |
| Bootstrap sin POS Profile | Error de configuración explícito, sin pantalla global oculta |
| Migrate repetido | Correcto |
| OpenSpec strict | Correcto |
| Python py_compile | Correcto |
| JavaScript node --check | Correcto |
| JSON jq | Correcto |

## Suite existente

Se habilitó allow_tests únicamente en v15.local y se ejecutó run-tests para la app. El runner intentó preparar datos estándar de ERPNext, pero el sitio preexistente carece del nodo raíz Department "All Departments"; produjo errores LinkValidationError durante la preparación. No se atribuye este error a restaurant_management y la suite existente no contiene aserciones funcionales suficientes.

La calificación completa requiere completar el dataset base del sitio o crear un sitio desechable totalmente nuevo, y agregar pruebas específicas de permisos, ciclo de órdenes, facturación e impresión.

## Configuración pendiente para prueba navegador

El sitio tiene Company "ADDERA PERU SAC", pero no tiene un POS Profile habilitado disponible para Administrator. El bootstrap v15 bloquea correctamente el inicio e informa esta condición. Para la prueba end-to-end se debe crear un POS Profile, almacén, cliente y apertura POS de prueba.

## Hallazgo tributario confirmado

Los campos Restaurant Settings denominan las variantes _m como "Serie Factura Manual" y "Serie Boleta Manual". El código 1.7.7 elige la variante manual cuando dinners == 1 y luego decide Boleta/Factura por el tipo de documento del cliente. Esta doble semántica debe reemplazarse por dos selecciones independientes:

- Tipo de comprobante: Boleta o Factura.
- Modo de emisión: Electrónica o Manual.

dinners quedará reservado para la cantidad de comensales. El cambio de selección de series se mantiene pendiente de confirmación funcional para no alterar emisión tributaria sin aprobación.
