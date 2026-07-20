# Baseline técnico para ERPNext v15

Fecha del inventario: 2026-07-20.

## Matriz soportada inicial

| Componente | Versión verificada | Contrato inicial |
|---|---:|---|
| Frappe | 15.109.0 | Requerido |
| ERPNext | 15.109.0 | Requerido |
| Python | 3.12.3 | Soportado por el bench validado |
| restaurant_management | 1.7.7 | Fork de partida |
| alphabit-technology/erpnext-restaurant | 1.8.6 (commit c55ac4a) | Referencia selectiva, no reemplazo completo |
| ovenube_peru | 15.3.5 (commit 9d5bee6) | Requerido mientras la emisión electrónica siga acoplada |
| silent_print | 0.0.1 (commit b855a03) | Requerido para comandas, boletas y facturas |
| WebApp Hardware Bridge | Configuración externa | Requerido para la impresión por tiketera |
| mfc | 0.0.1 en el bench actual | Dependencia a retirar de esta app |
| posawesome | No instalado | Referencias residuales a retirar o aislar |

La calificación inicial se limita a la serie v15 verificada. Otras versiones menores se agregarán a la matriz solo después de ejecutar la misma suite.

## Comparación por componente

| Área | Fork 1.7.7 | Upstream 1.8.6 | Decisión v15 |
|---|---|---|---|
| Helper frontend | Consume globals pero no incluye implementación | Incluye JS/CSS y DocTypes de Desk Form | Portar el subconjunto usado, conservando procedencia GPLv3 |
| Inicio del POS | Consulta POS Settings.is_online y oculta todo body | Mantiene el mismo patrón obsoleto | Sustituir por bootstrap servidor v15 y error acotado a la página |
| Sala y mesa | Contiene cambios TIDAX | Añade reservas, menús y otras funciones | Conservar delta TIDAX; no incorporar funciones nuevas no requeridas |
| Facturación | Cuatro ramas duplicadas, owner fijo y decisión parcial por dinners | Lógica diferente y sin todos los cambios locales | Refactor local; campo explícito Boleta/Factura; dinners solo comensales |
| Impresión | Llama silent_print directamente desde navegador | No representa toda la operación TIDAX local | Adaptador para silent_print/Hardware Bridge, persistencia previa y reintento |
| Producción | RM PRODUCTOS A PRODUCIR enlaza DocTypes MFC | No resuelve el modelo local | Crear DocType hijo propio y corregir amended_from |
| Ciclo Table Order | Es submittable, pero existen escrituras/commits directos | No es fuente segura para reemplazo total | Conservar is_submittable y usar submit/cancel |
| Seguridad | Guest, SQL interpolado, respuestas amplias y controles cliente | Conserva riesgos relevantes | Endurecer servidor por actor, rol, compañía, sala y documento |
| Reportes | Reportes TIDAX adicionales sin aislamiento completo | No contiene todos los reportes locales | Conservar y corregir filtros, permisos y calendario |
| Instalación | Fixtures no estándar y borrado directo after_migrate | Incluye helper pero hereda metadatos problemáticos | Fixtures filtrados y migraciones idempotentes |

El diff entre árboles afecta aproximadamente 201 archivos; por eso el upstream no se fusionará como bloque. Los componentes se portarán por capacidad y con pruebas específicas.

## Inventario de dependencias y metadatos

### Frontend

Globals requeridos: frappe.jshtml, frappeHelper, DeskForm, DeskModal y controles de formulario/numpad. El fork carga clusterize, interact, drag, RM.helper y object-manage, pero no carga los seis archivos helper que sí están en upstream.

Restaurant Manage carga dinámicamente las clases de sala, mesa, orden, cocina, pago y factura. El orden de carga debe ser determinista antes de construir la pantalla.

### Python y apps

No se detectaron imports Python directos de mfc, silent_print u ovenube_peru: la integración actual ocurre mediante rutas RPC y enlaces de metadatos. ovenube_peru y silent_print se conservarán como capacidades declaradas; posawesome y Work Station son referencias residuales que no pueden asumirse disponibles.

### DocTypes externos y campos

- RM PRODUCTOS A PRODUCIR apunta a MFC Pichanga Inscripcion Reporte Producto y MFC Pichanga Inscripcion Reporte.
- Table Order enlaza POS Invoice, POS Profile, Company, Customer, Address, Restaurant Object y Order Entry Item.
- Los Desk Forms son recursos de la app, pero falta el DocType Desk Form y su hijo Desk Form Field.
- La inicialización consulta POS Settings.is_online, campo ausente en v15.
- Los campos tributarios de Customer/POS Invoice utilizados por el fork pertenecen al contrato con ovenube_peru y deben verificarse en instalación.

### APIs y hallazgos de seguridad

Se localizaron métodos whitelisted en api.py, Restaurant Settings, Table Order Cambio Mozo, utils.py y la página Restaurant Manage.

| Hallazgo base | Requisito OpenSpec | Prueba requerida |
|---|---|---|
| get_settings_data permite Guest | Authenticated server operations | Guest recibe denegación |
| obtener_res_set acepta un campo arbitrario de tabSingles | Validated input and query construction | Campo fuera de allowlist es rechazado |
| SQL con f-strings o format | Validated input and query construction | Entradas maliciosas no alteran consulta |
| Cambio de mozo reescribe owner y hace commit | Authorized state-changing operations / Authentic audit ownership | Owner de auditoría se conserva |
| make_invoice fija cajero@resto.pe | Authentic audit ownership | El usuario autenticado queda en auditoría |
| Escrituras directas y commits internos | Atomic order mutations / Validated POS Invoice creation | Una excepción revierte toda la acción |
| Renderizado HTML de datos de órdenes | Safe client rendering | Texto HTML se muestra escapado |
| Reportes sin compañía consistente | Company-isolated reports | Dos compañías no mezclan resultados |
| Scheduler reescribe estados | Non-destructive expiry behavior | Estados terminales permanecen intactos |

## Decisiones ya confirmadas

- silent_print y WebApp Hardware Bridge se mantienen para comandas, boletas y facturas.
- Una falla de impresión no invalida la venta y permite reintento sin duplicación.
- La funcionalidad MFC se migra a DocTypes propios.
- Table Order conserva su ciclo submittable.
- dinners representa solo la cantidad de comensales.
- Boleta o Factura se seleccionará en un campo explícito.
- Está autorizado un sitio v15 desechable y la implementación en la rama feature/restaurant-v15-compatibility.

## Pendientes funcionales acotados

Falta confirmar qué representan las series con sufijo _m y validar los estados históricos de producción/cocina. Hasta resolverlo, esas series se preservarán sin cambiar su significado y no se usarán como sustituto del nuevo tipo de comprobante explícito.
