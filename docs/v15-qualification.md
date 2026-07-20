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
| Sincronizar voucher_type y emission_mode en Table Order | Correcto |
| Sincronizar ambos Select en payment-order | Correcto |
| Resolver las cuatro combinaciones de series | Correcto |
| Rechazar una combinación de comprobante desconocida | Correcto |
| Pruebas unitarias de matriz dentro de consola Frappe | 5 correctas |
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

Se habilitó allow_tests únicamente en v15.local y se ejecutó run-tests para la app y para Table Order. El runner intentó preparar datos estándar de ERPNext, pero el sitio preexistente carece de nodos raíz como Department "All Departments" y Supplier Group "All Supplier Groups"; produjo errores LinkValidationError antes de ejecutar las pruebas de la app. No se atribuye este error a restaurant_management.

Para aislar la nueva lógica se ejecutó `TestTableOrder` dentro de una consola inicializada de v15.local. Pasaron cinco pruebas: matriz de cuatro combinaciones, selecciones obligatorias, rechazo de combinaciones desconocidas, identidades válidas y rechazo de identidad incompatible.

La calificación completa requiere completar el dataset base del sitio o crear un sitio desechable totalmente nuevo, y agregar pruebas específicas de permisos, ciclo de órdenes, facturación e impresión.

## Configuración pendiente para prueba navegador

El sitio tiene Company "ADDERA PERU SAC", pero no tiene un POS Profile habilitado disponible para Administrator. El bootstrap v15 bloquea correctamente el inicio e informa esta condición. Para la prueba end-to-end se debe crear un POS Profile, almacén, cliente y apertura POS de prueba.

## Selección tributaria implementada

Los campos Restaurant Settings denominan las variantes _m como "Serie Factura Manual" y "Serie Boleta Manual". La doble semántica anterior fue reemplazada por dos selecciones obligatorias e independientes:

- Tipo de comprobante: Boleta o Factura.
- Modo de emisión: Electrónica o Manual.

`dinners` queda reservado para la cantidad de comensales. El servidor valida DNI para Boleta y RUC para Factura, selecciona una de las cuatro series configuradas y sólo contacta al proveedor electrónico en modo Electrónica. Los códigos preservados son 01/Factura, 03/Boleta, 1/DNI y 6/RUC, conforme a los catálogos 01 y 06 de SUNAT.

Referencia oficial: [Anexo E, Catálogos de códigos SUNAT](https://www.sunat.gob.pe/legislacion/superin/2017/anexoE-245-2017.pdf).

Limitación pendiente: `Restaurant Settings` es Single y las series siguen siendo globales. La resolución de series por compañía y contexto operativo aún no está implementada.
