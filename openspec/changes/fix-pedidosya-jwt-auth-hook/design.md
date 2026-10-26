## Architecture and verification

Graphify conecta authenticate_inbound con dispatch_order y update_order_status.
El código confirma que Frappe app.application llama validate_auth antes de API
dispatch. validate_auth ejecuta auth_hooks antes de rechazar Authorization Bearer
con usuario Guest. Se utilizará este punto de extensión sin modificar core.

El hook reconocerá rutas exactas /api/method/ y /api/v1/method/ para dispatch_order
(POST) y update_order_status (PUT/POST). No autenticará recursos REST, cmd de RPC
legado, rutas con sufijos ni otras APIs. En rutas reconocidas se rechazará cmd
que redirija y cualquier override que cambie el método efectivo: app.application
prioriza form_dict.cmd y handler.execute_cmd aplica overrides. No usar prefijos
amplios ni marcadores globales para omitir verificaciones.

Se obtendrá remote_id desde el mismo form_dict que consume el endpoint, exigiendo
texto no vacío, y se reutilizará la búsqueda de configuración habilitada. Después
de validar JWT y usuario se llamará set_user con el usuario técnico configurado.
Se conserva y restaura form_dict después del cambio: set_user lo vacía en Frappe
v15, por lo que de otro modo se perderían remote_id y los parámetros del pedido.
Se rechazará usuario inexistente/deshabilitado y los usuarios especiales Guest y
Administrator; no se concederán roles ni se crearán sesiones persistentes. La
validación IP nativa posterior al hook queda intacta.

## JWT and compatibility

Se permite solamente HS256/HS384/HS512. Se requieren exp y service=middleware;
issuer/audience se comprueban cuando están configurados. Leeway 0 se respeta,
usando el valor predeterminado solo cuando falta. Esto endurece el contrato
anterior que validaba exp solamente si venía presente; se documenta como cambio
de seguridad. Los JWT de prueba ya incluyen exp y service.
Se valida otra vez dentro del endpoint como defensa adicional. Las credenciales
permanecen en Password; no se imprimen JWT, payloads ni secretos en errores/logs.
No se cambian timeouts, reintentos ni callbacks salientes.

## Transactions, isolation and impact

El hook realiza únicamente lecturas y cambio de identidad local a la solicitud.
No hace commits ni crea órdenes; conserva las transacciones, idempotencia y cola
existentes. No cambia contabilidad, impuestos, precios, facturación, stock,
tiempo real, permisos de DocTypes ni migraciones. Ninguna autenticación de otra
ruta puede beneficiarse del JWT de PedidosYa.

## Validation and rollout

Revisión especializada requerida por AGENTS identificó el desvío cmd/override,
exp opcional y leeway 0. Se cubren con unittest y mocks, sin inicializar sitio ni
conectar a DB/Redis/HTTP. Se prueba validate_auth real de Frappe con proveedores
OAuth/API key externos simulados y el hook registrado de la app; se verifica
dispatch 202/200 con persistencia simulada. No usar bench run-tests en v15.local:
el runner de ERPNext puede borrar Item Price. No enviar pedidos a producción.

No requiere migrate ni build de frontend. Al desplegar en un sitio autorizado,
limpiar caché de hooks y recargar procesos según su modo de ejecución. No ejecutar
clear-cache/restart/migrate sin nueva autorización. Reversión: volver al código
anterior y refrescar hooks/procesos en ventana autorizada; sin reversión de datos.
