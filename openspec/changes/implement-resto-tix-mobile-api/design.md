## Context

El diseño previo `design-waiter-mobile-app` estableció que ERPNext debe continuar como fuente de verdad. La plataforma móvil confirmada usa React Native 0.86 y FastAPI, con PostgreSQL y Redis disponibles en `192.168.2.73`. El servidor móvil alcanza el bench por `192.168.2.53:8000` cuando selecciona explícitamente el sitio `v15.local`; esta ruta HTTP es solo de desarrollo.

Graphify ubicó `restaurant_manage.py`, `api.py`, `TableOrder`, `Restaurant Permission` y `Order Entry Item` en el núcleo del flujo. El código confirma que `TableOrder` ya concentra creación, cálculo, actualización de líneas, envío, sincronización, pago y eventos realtime. La nueva fachada debe delegar en esas reglas y no copiar sus cálculos.

## Architecture

```text
Resto Tix (React Native)
        |
        | HTTPS + OAuth2/PKCE + client_request_id
        v
Resto Tix BFF (FastAPI)
        |
        | token delegado + contrato interno versionado
        v
restaurant_management.mobile_api.v1
        |
        +-- permisos y contexto Frappe
        +-- Restaurant Object / mesas
        +-- Table Order / Order Entry Item
        +-- catálogo, precios e impuestos ERPNext
        `-- Production Center / realtime
```

FastAPI normaliza el contrato móvil, limita tasa y oculta detalles internos. No mantiene una base comercial paralela. PostgreSQL del proyecto móvil podrá guardar únicamente metadatos técnicos de dispositivos/auditoría; Redis podrá usarse para rate limiting y caché no autoritativa.

## Authentication and Authorization

- Usar OAuth 2.0 Authorization Code con PKCE provisto por Frappe.
- React Native almacenará tokens revocables en almacenamiento seguro; nunca contraseñas o API Secrets.
- FastAPI no emitirá una identidad comercial independiente: validará/delegará el token contra Frappe.
- Cada endpoint validará usuario habilitado, Company, POS Profile, ambiente, mesa y permiso sobre `Table Order`.
- Las capacidades devueltas al cliente son informativas; la autorización se repite en cada mutación.
- HTTP por IP se admite únicamente en QA dentro de la LAN. Producción requiere dominio HTTPS válido.

## Proposed Frappe API

Namespace: `restaurant_management.mobile_api.v1`.

| Método | Uso | Mutación |
|---|---|---|
| `get_context` | usuario, empresas, perfiles y capacidades | no |
| `get_tables` | ambientes, mesas y órdenes activas autorizadas | no |
| `get_catalog` | búsqueda/paginación y precio autoritativo | no |
| `get_order` | orden completa y versión vigente | no |
| `open_order` | crear o recuperar orden de una mesa | sí |
| `mutate_item` | agregar, cambiar cantidad/nota o retirar | sí |
| `send_command` | confirmar líneas y rutas de producción | sí |
| `get_changes` | reconciliación acotada desde un marcador | no |

Las funciones whitelisted serán `POST` para mutaciones y no aceptarán nombres de métodos o DocTypes enviados por el cliente.

## Contract Envelope

Respuesta exitosa:

```json
{
  "data": {},
  "order_version": "2026-09-11T00:00:00.000000",
  "server_time": "2026-09-11T00:00:00Z"
}
```

Error estable:

```json
{
  "error": {
    "code": "ORDER_VERSION_CONFLICT",
    "message": "La orden cambió en otro dispositivo.",
    "retryable": false,
    "current_order": {}
  }
}
```

No se devolverán trazas, SQL, tokens ni datos de clientes ajenos al pedido autorizado.

## Idempotency and Concurrency

- Toda mutación recibe UUID `client_request_id`, acción, orden y `expected_order_version`.
- La unicidad mínima será usuario + `client_request_id`.
- El registro persistente guardará estado, hash canónico de la solicitud, referencia de orden, respuesta mínima y caducidad.
- Reutilizar la clave con otro payload será rechazado.
- La orden se bloqueará mediante `SELECT ... FOR UPDATE` dentro de la transacción antes de verificar versión y mutar.
- El resultado idempotente quedará confirmado en la misma transacción que el cambio comercial.
- No se introducirán `frappe.db.commit()` manuales.

El DocType técnico `Restaurant Mobile Request` usa `request_key` como nombre único interno (SHA-256 de usuario + UUID), conserva `client_request_id`, usuario, orden, acción, hash canónico, estado `Processing`/`Completed`, fechas de solicitud/finalización/caducidad y la respuesta JSON mínima. Solo `System Manager` tiene acceso directo; la fachada lo administra internamente con permisos ignorados de forma acotada. La retención inicial es de siete días y su limpieza programada se difiere hasta validar la política operativa del piloto.

## Realtime and Reconciliation

Los eventos existentes ayudan a actualizar la UI, pero no son fuente de verdad. El API devolverá una versión/marca verificable y `get_changes` permitirá refrescar mesas u órdenes afectadas al volver del segundo plano o perder eventos. El MVP podrá usar sondeo acotado desde FastAPI mientras se califica Socket.IO en React Native.

## Files Implemented

- `restaurant_management/mobile_api/v1.py` y pruebas unitarias cercanas.
- Metadata y controlador de `Restaurant Mobile Request`.
- Contrato externo `docs/openapi/resto-tix-v1.yaml` para el BFF FastAPI.
- Sin cambios en `hooks.py`; la limpieza programada queda para un incremento posterior.

No se prevén cambios en `electronic_invoice.py`, reportes, fixtures tributarios ni apps core.

## Test Matrix

| Área | Casos mínimos |
|---|---|
| Autenticación | token válido, expirado, revocado y usuario deshabilitado |
| Alcance | ambiente permitido/no permitido, otra Company y otro POS Profile |
| Catálogo | paginación, búsqueda, ítem no vendible y paridad de precio/impuesto web |
| Orden | abrir libre, recuperar activa, comensales y cliente predeterminado |
| Línea | alta, cantidad, nota, retiro permitido y línea ya enviada |
| Idempotencia | doble toque, timeout/reintento y misma clave con payload distinto |
| Concurrencia | versión obsoleta y dos dispositivos sobre la misma mesa |
| Cocina | envío único, P3/P5 y estados de preparación |
| Seguridad | nombres arbitrarios de DocType/método, acceso cruzado y payload inválido |
| Regresión | Restaurant Manage, impresión, precuenta y flujo POS existente |

## Rollback

1. Deshabilitar en FastAPI las rutas de Resto Tix.
2. Revocar el cliente OAuth y tokens móviles.
3. Revertir el paquete `mobile_api` sin tocar órdenes ya creadas correctamente.
4. Deshabilitar y luego retirar el DocType técnico mediante una migración posterior y explícita; no borrar registros transaccionales durante una reversión inmediata.
5. Mantener `Restaurant Manage` como canal operativo durante todo el despliegue gradual.

## Risks and Mitigations

- **Comandas duplicadas:** idempotencia persistente y pruebas de timeout.
- **Edición concurrente:** bloqueo de fila y versión optimista.
- **Acceso cruzado:** validación contextual en cada endpoint y pruebas negativas.
- **Divergencia de cálculos:** delegación en `TableOrder` y comparación automática con web.
- **Dependencia de red:** reconciliación; no se confirma cocina sin respuesta del servidor.
- **HTTP interno actual:** limitar a QA y bloquear publicación productiva hasta disponer de HTTPS.
- **Sitio por Host header:** configurar un origen estable; no depender de que una IP resuelva al sitio correcto.
