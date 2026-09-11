## Why

`restaurant_management` no dispone de una API móvil versionada y acotada para el trabajo del mozo. La interfaz web actual usa métodos de documentos y eventos internos que no deben exponerse directamente a un cliente móvil ni reproducirse en FastAPI.

Resto Tix necesita consumir mesas, catálogo, órdenes y comandas desde React Native, manteniendo en ERPNext la autoridad sobre permisos, precios, impuestos, estados y documentos.

## Objective

Implementar en `restaurant_management` una fachada REST segura para el MVP Android de Resto Tix, consumida por el BFF FastAPI del servidor móvil y compatible con Frappe/ERPNext v15.

## Scope

- Contexto autenticado, Companies, POS Profiles y capacidades permitidas.
- Ambientes y mesas autorizados, con orden activa y estado vigente.
- Catálogo paginado calculado por las reglas actuales de ERPNext.
- Apertura y consulta de `Table Order`.
- Alta, cambio de cantidad, notas y retiro permitido de líneas no enviadas.
- Envío idempotente de comandas a Production Center.
- Consulta/reconciliación de estados de orden y cocina.
- Control optimista de concurrencia e idempotencia persistente.
- Pruebas de permisos, contratos, reintentos, conflictos y regresión web.

## Exclusions

- Pago, POS Invoice y facturación electrónica móvil.
- Operación offline definitiva, push, cámara, códigos de barras o impresión móvil.
- Cambios en precios, impuestos, descuentos, SUNAT u `ovenube_peru`.
- Acceso genérico del cliente a `/api/resource` o a métodos arbitrarios de documentos.
- Persistir pedidos, clientes, precios o impuestos comerciales en FastAPI/PostgreSQL.
- Modificar `frappe` o `erpnext`.

## Affected Application and Components

- App: `restaurant_management`.
- Módulos: API, Restaurant Manage y dominio de órdenes.
- DocTypes: `Restaurant Permission`, `Restaurant Company Settings`, `Restaurant Object`, `Table Order`, `Order Entry Item` y el nuevo registro técnico `Restaurant Mobile Request`.
- APIs: nueva fachada versionada `restaurant_management.mobile_api.v1`.
- Hooks: solo si son necesarios para registrar o limpiar idempotencia; cualquier hook se documentará antes de implementarlo.
- Fixtures/patches: no previstos; un nuevo DocType requerirá metadata versionada y migración estándar.
- Reportes y facturación electrónica: sin cambios.

## Expected Impact

- El cliente móvil operará sobre el mismo pedido que `Restaurant Manage`.
- Los reintentos no duplicarán platos ni comandas.
- Un usuario no podrá consultar o mutar otra Company, POS Profile, ambiente o mesa.
- El frontend web conservará su comportamiento actual.

## Risk

**Medio-alto.** Se agregará una superficie API autenticada y mutaciones concurrentes sobre órdenes activas. No se modifica facturación en este incremento, pero una comanda duplicada o una autorización insuficiente afectaría la operación del restaurante.

## Acceptance Criteria

- OpenAPI y errores del contrato están definidos y versionados.
- Todos los endpoints requieren autenticación y vuelven a validar permisos en el servidor.
- ERPNext calcula precios, impuestos, totales y rutas de producción.
- Cada mutación exige `client_request_id` y versión esperada de la orden.
- Repetir una solicitud confirmada devuelve el resultado previo sin repetir el efecto.
- Una versión obsoleta devuelve conflicto y el estado autoritativo actual.
- Dos usuarios o dispositivos no sobrescriben silenciosamente la misma orden.
- Las pruebas de `Restaurant Manage`, órdenes, impresión y cocina permanecen verdes.
