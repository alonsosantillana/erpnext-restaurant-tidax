## Context

`Restaurant Manage` ya usa `Restaurant Object` y `Restaurant Permission` para mostrar ambientes y mesas, `Table Order` como raiz comercial y `Order Entry Item` para las lineas que llegan a Production Center. El cliente predeterminado se obtiene del `POS Profile`, y el pago esta protegido por una capacidad configurable y validacion de servidor.

Graphify se consulto como mapa estructural local y los hallazgos se contrastaron con `restaurant_manage.py`, `restaurant_manage.js`, `api.py`, `table_order.py` y sus pruebas. La aplicacion movil debe integrarse con esos limites de dominio, no copiar su implementacion de interfaz.

## Goals / Non-Goals

**Goals:**

- Disponer de una experiencia movil rapida y segura para el mozo.
- Mantener ERPNext como fuente de verdad de permisos, precios, impuestos, estado y documentos.
- Tolerar reintentos, doble toque y cortes breves de red.
- Conservar compatibilidad total con el frontend web.

**Non-Goals:**

- Crear un backend paralelo.
- Autorizar pagos o comprobantes fuera de linea.
- Guardar secretos del servidor en el dispositivo.
- Incluir administracion de cocina, produccion, contabilidad o inventarios en el MVP.

## Decisions

### 1. Fachada movil de casos de uso

El backend expondra metodos acotados para contexto, ambientes/mesas, catalogo, orden, lineas, comandas, estados y precuenta. El cliente no recibira permisos genericos para construir documentos arbitrarios mediante `/api/resource`.

La fachada llamara la logica de dominio actual o servicios extraidos de ella. `Restaurant Manage` y la app movil compartiran reglas; no se implementaran dos calculos de totales.

### 2. Autenticacion

Se preferira OAuth 2.0 Authorization Code con PKCE. Los tokens se almacenaran usando el almacen seguro del dispositivo, tendran expiracion y podran revocarse. HTTPS con certificado valido es una precondicion de produccion.

Una alternativa basada en credenciales embebidas o API Secret queda descartada.

### 3. Autorizacion por capacidad y contexto

Cada lectura y mutacion validara usuario, Company, POS Profile, ambiente y mesa. El backend devolvera capacidades explicitas como `can_create_order`, `can_send_command`, `can_request_prebill` y `can_pay`; la interfaz las usara para presentacion, pero el servidor las volvera a validar al ejecutar.

### 4. Consistencia e idempotencia

Cada mutacion movil usara un `client_request_id` unico. La version de la orden o su valor `modified` servira como precondicion optimista. Las mutaciones sensibles bloquearan la orden y devolveran su estado posterior al commit.

Un reintento con la misma clave devolvera el resultado anterior. Una operacion nueva basada en una version obsoleta devolvera conflicto y la orden vigente.

### 5. Offline limitado

La app mantendra una cache local y una cola cifrada. En el MVP solo se prepararan offline cambios sobre ordenes previamente cargadas; ninguna comanda se considerara enviada hasta confirmacion del servidor. Pago, factura y anulaciones sensibles requeriran conexion.

### 6. Realtime con reconciliacion

Realtime notificara cambios, pero no sera la fuente final. Despues de reconectar, volver del segundo plano o detectar saltos de version, la app consultara cambios incrementales y recargara las ordenes afectadas.

### 7. Cliente movil desacoplado del generador

El contrato funcional sera independiente de Flutter, React Native, Ionic, Android nativo o PWA. La seleccion se realizara despues de una prueba tecnica que demuestre OAuth/PKCE, almacenamiento seguro, cola local, realtime, compilacion firmada y propiedad del codigo.

## API Surface Proposed

| Dominio | Operaciones |
|---|---|
| Sesion | login OAuth, refresh/revoke, contexto y capacidades |
| Restaurante | ambientes y mesas permitidos, estado y orden activa |
| Catalogo | busqueda paginada con precio/impuesto autoritativo |
| Orden | abrir, consultar y sincronizar |
| Lineas | agregar, cambiar cantidad/notas y retirar si es valido |
| Cocina | confirmar/envio idempotente y consultar estados |
| Comercial | cliente predeterminado, precuenta y pago autorizado posterior |

Los contratos detallados, codigos de error y versionado se publicaran como OpenAPI antes de construir el cliente.

## DocTypes and Components Affected in Implementation

- `Restaurant Permission`: lectura de alcance del usuario.
- `Restaurant Company Settings`: configuraciones operativas y capacidades.
- `Restaurant Object`: ambientes, mesas y centros de produccion.
- `Table Order`: raiz transaccional y bloqueo de concurrencia.
- `Order Entry Item`: cantidades, notas y estados.
- `Customer` y `POS Profile`: cliente predeterminado y contexto comercial.
- `POS Invoice`: solo en fase de pago autorizado.
- `restaurant_management/api.py`: autorizacion y posible punto de entrada de la fachada.
- pagina `restaurant_manage`: referencia funcional y regresion, no dependencia de UI.

No se proponen DocTypes, hooks, fixtures ni patches definitivos hasta completar la evaluacion tecnica. Podria requerirse un DocType de registro de dispositivo o idempotencia; esa decision se especificara antes de implementarlo.

## Security and Privacy

- No registrar tokens, DNI/RUC, telefonos, direcciones ni payloads completos.
- Enmascarar datos personales en listas y notificaciones.
- Proteger endpoints contra acceso cruzado de compania/perfil/ambiente.
- Aplicar limites de tasa y alertas ante actividad anomala.
- Mantener auditoria de actor, dispositivo y hora en acciones relevantes.
- Revocar sesiones al deshabilitar el usuario o retirar el dispositivo.

## Test Matrix

| Area | Casos minimos |
|---|---|
| Permisos | mozo autorizado, ambiente no autorizado, otro POS Profile y usuario deshabilitado |
| Orden | abrir, recuperar activa, cliente predeterminado, comensales y nueva ronda |
| Catalogo | precios/impuestos iguales a web, paginacion, busqueda e Item no vendible |
| Mutaciones | doble toque, reintento, version obsoleta y dos dispositivos |
| Notas | escritura rapida, segundo plano, realtime concurrente y texto completo en cocina |
| Cocina | envio unico, ruteo P3/P5 y cambio de estados |
| Red | perdida antes/durante/despues del envio, reconexion y cola ordenada |
| Pago | boton oculto/visible, rechazo de servidor y emision conectada sin espera infinita |
| Seguridad | token expirado/revocado, dispositivo perdido y acceso cruzado |
| Regresion | mismo pedido desde web, impresion, caja y Production Center |

## Risks / Trade-offs

- **Conectividad local:** publicar solo una IP limita movilidad y certificados; produccion requiere dominio HTTPS o una red privada administrada.
- **Offline:** aumenta complejidad y conflictos; por eso pago y envio definitivo quedan conectados en el MVP.
- **Generador propietario:** puede limitar seguridad o mantenimiento; la prueba tecnica debe verificar exportacion y propiedad del codigo.
- **Concurrencia:** dos dispositivos pueden editar una mesa; versionado e idempotencia son obligatorios.
- **Realtime movil:** el sistema operativo puede suspender conexiones; siempre se requiere reconciliacion al reabrir.
- **Datos personales:** la cache local aumenta exposicion; se minimizara, cifrara y eliminara al cerrar sesion.

## Rollback

1. Deshabilitar el acceso de clientes moviles sin deshabilitar `Restaurant Manage`.
2. Revocar clientes OAuth y sesiones de dispositivos.
3. Revertir endpoints de fachada manteniendo lectura de auditoria mientras sea necesaria.
4. Conservar `Table Order`, comandas, POS Invoice y demas documentos creados correctamente.
5. No eliminar documentos transaccionales como parte de una reversion de la app.

## Open Questions

- Nombre, version y documentacion del servidor generador.
- Plataformas objetivo y versiones minimas.
- Uso exclusivo en LAN, VPN o acceso por Internet.
- Pago incluido o excluido del MVP.
- Impresion desde el dispositivo o por estaciones existentes.
- Tiempo maximo de operacion sin red.
- Politica de sesiones simultaneas por usuario.
- Requisitos de distribucion: privada, MDM, Play Store o App Store.

