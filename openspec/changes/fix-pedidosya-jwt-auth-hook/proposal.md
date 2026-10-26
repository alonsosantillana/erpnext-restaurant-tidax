## Why

El webhook PedidosYa recibe un JWT Bearer propio, pero Frappe valida Authorization
antes de despachar la API. Al no existir auth_hooks para esta integración, una
solicitud sin cookies se rechaza con AuthenticationError antes de validar el JWT
en dispatch_order. Se reprodujo el conflicto con un JWT ficticio válido y mocks.

## What Changes

- Registrar un hook estándar de autenticación exclusivo para las dos APIs PedidosYa.
- Validar configuración habilitada, firma, algoritmo, expiración, servicio y usuario
  técnico antes de establecer la identidad de la solicitud.
- Bloquear redirecciones mediante cmd u overrides hacia otros métodos.
- Conservar la validación JWT dentro de los endpoints y sus contratos 202/200.
- Añadir pruebas sin BD del límite Frappe/API y regresión de PedidosYa.

## Impact and scope

Solo restaurant_management en desarrollo 192.168.2.53, rama principal master y rama
de trabajo fix/pedidosya-jwt-auth-hook. Riesgo alto: autenticación e integración.
El usuario autorizó expresamente la corrección únicamente en desarrollo.
Archivos: hooks.py, integrations/pedidosya/auth.py, api.py, pruebas y documentación.
Sin cambios en core, otras apps, roles, DocTypes, fixtures, esquema o precios.
No desplegar ni cambiar configuración/datos de resto.v1.tidax.pe. No hacer merge
ni publicación remota en este alcance; dejar el cambio local revisable.

## Acceptance

Un JWT válido alcanza el endpoint sin cookies de administrador. JWT inválidos,
configuraciones deshabilitadas, usuarios inválidos y desvíos de rutas/métodos no
adquieren identidad técnica ni persisten pedidos. Las demás APIs conservan su
autenticación normal. La prueba test=true no crea documentos comerciales.
