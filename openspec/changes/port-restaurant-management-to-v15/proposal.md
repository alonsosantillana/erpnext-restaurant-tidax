## Why

El fork `restaurant_management` 1.7.7 no puede operar de forma completa en un sitio Frappe/ERPNext 15 estandar: no integra las utilidades frontend que consume, consulta campos obsoletos, depende de DocTypes y apps no declarados, y contiene rutas de seguridad e integridad incompatibles con una operacion POS confiable. Se requiere un port selectivo a v15 que preserve las personalizaciones TIDAX/SUNAT sin adoptar indiscriminadamente todos los cambios del upstream 1.8.6.

## Objective

Entregar una version instalable, segura y verificable de `restaurant_management` para Frappe/ERPNext 15, con flujos atomicos de sala, mesa, comanda, pago y `POS Invoice`, dependencias explicitas y pruebas de regresion sobre un sitio aislado.

## What Changes

- Integrar localmente las utilidades frontend requeridas (`frappe.jshtml`, `frappeHelper`, formularios y modales) o sustituirlas por APIs estandar v15 con el menor cambio funcional posible.
- Eliminar la dependencia de campos obsoletos de `POS Settings` y adaptar la inicializacion del POS a ERPNext 15.
- Formalizar y validar dependencias con `ovenube_peru`, `silent_print` y WebApp Hardware Bridge; reemplazar los DocTypes provenientes de `mfc` por modelos propios de la app y retirar referencias residuales a dependencias no usadas.
- Corregir APIs whitelisted, permisos, consultas SQL, aislamiento por compania y renderizado de valores no confiables.
- Corregir el ciclo de vida de `Table Order` y `Order Entry Item`: eliminacion, envio a cocina, finalizacion, transferencia, cambio de mozo, facturacion y limpieza programada.
- Sustituir cambios directos de `docstatus`, `owner` y commits parciales por ciclos documentales y transacciones consistentes.
- Separar configuracion tributaria de valores hardcodeados y seleccionar Boleta o Factura mediante un campo explicito, independiente de `guest_count`, preservando descuentos, gratuidad e integracion SUNAT.
- Corregir reportes operativos para respetar compania, fechas, estados documentales y permisos.
- Crear pruebas unitarias, de integracion, seguridad e instalacion para Frappe/ERPNext 15, ademas de una matriz funcional end-to-end.
- Documentar dependencias, instalacion, configuracion, reversion y resultados de pruebas.

El cambio es de **riesgo alto** porque afecta permisos, ordenes activas, estados de cocina, pagos, `POS Invoice`, facturacion electronica, datos existentes y dependencias entre apps.

## Scope

- App afectada: `restaurant_management`.
- Modulos: pagina Restaurant Manage, salas y mesas, ordenes, cocina, pagos, configuracion, permisos, gastos, cambio de mozo, produccion y reportes.
- DocTypes principales: `Restaurant Object`, `Table Order`, `Order Entry Item`, `Restaurant Settings`, `Restaurant Permission Manage`, `Resto Gastos`, `RM PRODUCTOS A PRODUCIR` y `Table Order Cambio Mozo`.
- Integraciones: ERPNext POS, stock, `POS Invoice`, `Material Request`, `ovenube_peru`, `silent_print` y WebApp Hardware Bridge. La funcionalidad de produccion que dependia de MFC se implementara con DocTypes propios.
- Hooks y artefactos: `hooks.py`, instalacion, scheduler, assets frontend, Custom Fields, Client Scripts, fixtures y posibles patches idempotentes.
- APIs: `restaurant_management.api`, metodos de pagina, metodos de documentos y utilidades whitelisted.
- Reportes y dashboards versionados por la app.

## Exclusions

- No se modificara codigo core de `frappe` ni `erpnext`.
- No se incorporaran automaticamente funcionalidades nuevas del upstream como reservas, menus o delivery por sucursal, salvo que sean imprescindibles para resolver una dependencia tecnica y se documenten como desviacion.
- No se reemplazara la interfaz completa ni se realizara una reescritura tecnologica.
- No se instalaran apps, ejecutaran migraciones, patches, reinicios ni cambios de datos en sitios existentes sin autorizacion explicita.
- No se cambiaran reglas tributarias, series ni payloads SUNAT sin validacion funcional y tributaria independiente.

## Capabilities

### New Capabilities

- `restaurant-v15-runtime`: Instalacion, dependencias, assets e inicializacion del POS compatibles con Frappe/ERPNext 15.
- `restaurant-access-security`: Autorizacion, aislamiento de datos, SQL seguro y renderizado protegido para operaciones y APIs del restaurante.
- `restaurant-order-lifecycle`: Ciclo atomico y coherente de mesas, ordenes, comandas, estados de cocina, transferencias y eliminaciones.
- `restaurant-pos-compliance`: Generacion de pagos y `POS Invoice` con trazabilidad, configuracion TIDAX/SUNAT e integraciones controladas.
- `restaurant-reporting-validation`: Reportes aislados por compania y estrategia de pruebas automatizadas y end-to-end para v15.

### Modified Capabilities

No existen especificaciones base previas en `openspec/specs/`; todas las capacidades se documentan inicialmente como nuevas.

## Expected Impact

- El POS podra instalarse y abrirse en un sitio v15 que cumpla las dependencias declaradas.
- Las operaciones sensibles dejaran de depender de parametros cliente sin validar, SQL interpolado y actualizaciones directas que omiten permisos.
- Ordenes, estados de cocina, pagos y facturas mantendran atomicidad y trazabilidad del usuario real.
- Los reportes no mezclaran informacion entre companias.
- La adopcion requerira pruebas sobre una copia representativa y puede requerir patches idempotentes para normalizar metadatos o datos existentes.

Archivos con impacto principal:

- `restaurant_management/hooks.py` y `restaurant_management/setup/install.py`.
- `restaurant_management/restaurant_management/page/restaurant_manage/`.
- `restaurant_management/public/js/` y `restaurant_management/public/restaurant/`.
- `restaurant_management/restaurant_management/doctype/restaurant_object/`.
- `restaurant_management/restaurant_management/doctype/table_order/`.
- `restaurant_management/restaurant_management/doctype/utils.py`.
- `restaurant_management/api.py`.
- DocTypes, fixtures, patches, reportes y pruebas relacionados.

## Acceptance Criteria

- La app se instala y migra sin errores en un sitio aislado con Frappe/ERPNext 15 soportado.
- `restaurant-manage` carga sin errores de consola o servidor y sin depender de campos inexistentes.
- Un usuario solo ve y modifica companias, salas, mesas, ordenes y facturas autorizadas.
- No quedan consultas SQL construidas con valores cliente sin parametrizar en el alcance del cambio.
- El ciclo mesa -> orden -> comanda -> completado -> pago -> `POS Invoice` es atomico y conserva auditoria, permisos y estados validos.
- Boleta, factura, descuentos y gratuidad conservan los resultados tributarios aprobados; fallos de SUNAT o impresion quedan controlados y no corrompen la venta.
- Los reportes aplican compania, fechas, `docstatus` y permisos de forma consistente.
- Las pruebas automatizadas criticas y la matriz end-to-end v15 quedan ejecutadas y documentadas antes de proponer despliegue.
- No se modifican apps core ni se hardcodean usuarios, empresas, sitios, credenciales o series operativas.
