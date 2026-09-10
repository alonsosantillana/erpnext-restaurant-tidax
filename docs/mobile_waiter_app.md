# Aplicacion movil para mozos

## 1. Proposito

Crear una aplicacion movil especializada para que los mozos registren y administren pedidos de restaurante usando las mismas reglas, datos y documentos de `restaurant_management` y ERPNext.

La aplicacion sera un cliente del sistema actual. No tendra una base de datos comercial independiente ni implementara un segundo motor de precios, impuestos, permisos, comandas o facturacion.

## 2. Objetivos operativos

- Reducir el tiempo entre la toma del pedido y su recepcion en cocina o bar.
- Mostrar al mozo solo los ambientes, mesas y perfiles POS para los que tiene acceso.
- Mantener precios, impuestos, clientes, stock, produccion y facturacion bajo control del servidor ERPNext.
- Permitir continuar tomando pedidos durante interrupciones breves de conectividad sin duplicar lineas ni comandas.
- Registrar usuario, dispositivo, fecha y resultado de cada operacion relevante.

## 3. Alcance del MVP

La primera version debe incluir:

1. Inicio y cierre de sesion seguro.
2. Seleccion de compania y perfil POS autorizado cuando exista mas de uno.
3. Lista de ambientes y mesas permitidas con su estado actual.
4. Apertura de una mesa usando el cliente predeterminado configurado.
5. Registro del numero de comensales.
6. Busqueda de productos por codigo, nombre y grupo.
7. Visualizacion del precio vigente y disponibilidad operativa.
8. Alta, cambio de cantidad y eliminacion de lineas aun no enviadas.
9. Notas por plato, por ejemplo `sin cebolla` o `traer hielo`.
10. Envio de la comanda a los centros de produccion configurados.
11. Seguimiento de estados: pendiente, en preparacion y terminado.
12. Adicion de nuevas rondas a una orden activa.
13. Consulta y solicitud de precuenta.
14. Cobro solo cuando la configuracion y el rol del mozo lo permitan.
15. Actualizacion en tiempo real con reconciliacion contra el servidor.

Quedan fuera del MVP:

- Cambiar la logica tributaria o de facturacion electronica.
- Administrar BOM, produccion, almacenes o contabilidad desde la app del mozo.
- Modificar precios maestros o conceder descuentos no autorizados.
- Ejecutar pagos o emitir comprobantes sin conexion.
- Conectarse directamente a MariaDB.
- Crear una aplicacion independiente para cocina, caja o reparto.

## 4. Flujo principal

```text
Inicio de sesion
    -> ambientes permitidos
    -> seleccion de mesa
    -> apertura o recuperacion de Table Order
    -> cliente predeterminado y comensales
    -> productos, cantidades y notas
    -> confirmacion de comanda
    -> envio a Production Center
    -> seguimiento de preparacion
    -> nueva ronda o solicitud de precuenta
    -> pago opcional segun permiso
```

El servidor sigue siendo la fuente de verdad. Un cambio local solo se considera confirmado cuando la API devuelve el documento persistido y su version actual.

## 5. Arquitectura objetivo

```text
Aplicacion Android/iOS/PWA
        |
        | HTTPS + autenticacion + idempotencia
        v
API movil de restaurant_management
        |
        +-- permisos de usuario, Company y POS Profile
        +-- Restaurant Object / ambientes / mesas
        +-- Table Order / Order Entry Item
        +-- Customer y cliente predeterminado
        +-- precios e impuestos ERPNext
        +-- Production Center y realtime
        +-- precuenta, pago y POS Invoice
```

La API movil sera una fachada de casos de uso. No se recomienda exponer al cliente movil acceso generico e irrestricto a `/api/resource`, porque obligaria a replicar reglas de negocio en el dispositivo y ampliaria innecesariamente los permisos.

## 6. Contratos de API requeridos

Los nombres definitivos se fijaran durante la implementacion, pero la interfaz funcional debe cubrir:

| Caso de uso | Entrada minima | Respuesta minima |
|---|---|---|
| Contexto del usuario | sesion | usuario, roles, companias, perfiles POS y capacidades |
| Ambientes y mesas | Company, POS Profile | ambientes permitidos, mesas, estado y orden activa |
| Catalogo | perfil, lista de precios, busqueda, paginacion | codigo, nombre, imagen, grupo, UOM, precio e impuestos resumidos |
| Abrir orden | mesa, comensales, `client_request_id` | `Table Order`, cliente, version y totales |
| Consultar orden | nombre de orden | cabecera, lineas, notas, estados, version y totales |
| Mutar linea | orden, operacion, cantidad/notas, version, `client_request_id` | orden autoritativa y version nueva |
| Enviar comanda | orden, lineas, version, `client_request_id` | lineas enviadas y destinos de produccion |
| Estado de cocina | orden o suscripcion | estados y marcas de tiempo por linea |
| Precuenta | orden | trabajo de impresion o representacion autorizada |
| Pago opcional | orden, medios de pago, cliente, idempotencia | resultado, POS Invoice y estado electronico independiente |
| Sincronizacion | ultima marca conocida | cambios autorizados posteriores y estado vigente |

Toda mutacion debe:

- validar permisos en el servidor;
- comprobar Company, POS Profile, ambiente y mesa;
- usar `client_request_id` para impedir duplicados por doble toque o reintento;
- detectar conflictos con una version o marca `modified`;
- ejecutarse en una transaccion;
- devolver el estado autoritativo posterior al commit.

## 7. Autenticacion y seguridad

- Publicar el servicio mediante un dominio HTTPS valido; la IP HTTP local solo debe usarse en desarrollo controlado.
- Preferir OAuth 2.0 Authorization Code con PKCE para dispositivos moviles.
- No incluir contrasenas, API Secret, claves de Nubefact ni credenciales de base de datos dentro de la app.
- Guardar tokens en el almacenamiento seguro del sistema operativo.
- Permitir revocar una sesion o dispositivo sin deshabilitar necesariamente al usuario.
- Aplicar expiracion de sesion y bloqueo luego de intentos fallidos.
- Minimizar datos de clientes en listas y eventos realtime.
- Validar en servidor la configuracion `mozo puede pagar`; ocultar el boton no es una medida de seguridad suficiente.
- Registrar actor, dispositivo y hora para apertura, envio, anulacion, descuento y pago.

## 8. Operacion sin conexion

La app debe distinguir tres estados visuales:

- **Guardado:** confirmado por ERPNext.
- **Pendiente de sincronizar:** permanece en una cola local cifrada.
- **Con conflicto o error:** requiere correccion o recarga antes de reenviar.

En el MVP se admite fuera de linea solamente la preparacion local de cambios de una orden ya conocida. El envio definitivo de comandas, el pago y la facturacion requieren conexion confirmada.

La cola local debe conservar `client_request_id`, orden, operacion, fecha del dispositivo y version base. Al recuperar conexion se procesa en orden y se detiene ante un conflicto para no sobrescribir cambios de otro mozo.

## 9. Tiempo real

La aplicacion debe recibir cambios de mesa, orden y cocina mediante el mecanismo realtime de Frappe cuando este disponible. Tambien debe implementar:

- reconexion con espera progresiva;
- consulta incremental al volver de segundo plano;
- sondeo como respaldo cuando el canal realtime no este disponible;
- deduplicacion de eventos;
- recarga acotada de la orden afectada, no de toda la aplicacion.

## 10. Experiencia del mozo

- Botones y textos con tamano adecuado para uso de pie y con una sola mano.
- Estado de mesa reconocible por texto e icono, no solo por color.
- Catalogo con imagen opcional y carga progresiva.
- Acciones frecuentes accesibles en uno o dos toques.
- Confirmacion antes de enviar una comanda o eliminar una linea enviada.
- Bloqueo visible durante una mutacion para evitar dobles toques.
- Notas que no se pierdan durante actualizaciones realtime.
- Indicador permanente de conexion y sincronizacion.
- Mensajes de error en lenguaje operativo y con accion de recuperacion.

## 11. Compatibilidad con el sistema actual

La implementacion debe reutilizar y validar contra:

- `Restaurant Permission` para acceso a ambientes.
- `Restaurant Company Settings` y `POS Profile` para configuracion por compania.
- `Restaurant Object` para ambientes, mesas y centros de produccion.
- `Table Order` como raiz comercial de la orden.
- `Order Entry Item` para platos, cantidades, notas y estado de preparacion.
- `Customer` y el cliente predeterminado del perfil POS.
- las reglas actuales de precios, impuestos, descuentos y moneda.
- la autorizacion configurable del mozo para pagar.
- el flujo existente de precuenta, `POS Invoice`, impresion y facturacion electronica.

## 12. Datos requeridos del generador de aplicaciones

Antes de implementar se debe entregar:

- nombre, version y documentacion del servidor generador;
- tecnologia generada: Flutter, React Native, Ionic, Android nativo o PWA;
- forma de importar el proyecto: Git, plantilla, ZIP o especificacion;
- plataformas y versiones de Android/iOS soportadas;
- mecanismo de compilacion, firma, publicacion y actualizacion;
- soporte para OAuth/PKCE, almacenamiento seguro, base local y WebSocket/Socket.IO;
- soporte para notificaciones, camara, codigo de barras e impresion;
- restricciones de licenciamiento y propiedad del codigo generado;
- ambientes de desarrollo, pruebas y produccion;
- procedimiento para almacenar secretos de compilacion sin incorporarlos al repositorio.

Tambien se debe definir:

- si la app sera Android, iOS o ambas;
- modelos y versiones minimas de los dispositivos;
- si se usara solo dentro de la red local o desde Internet;
- identidad visual y nombre comercial;
- si el MVP permite cobrar;
- si imprime desde el dispositivo o mediante estaciones existentes;
- duracion maxima esperada de una interrupcion de red;
- politica de una cuenta en varios dispositivos.

## 13. Fases propuestas

### Fase 0: descubrimiento

- Evaluar el generador y producir una aplicacion de prueba firmada.
- Validar HTTPS, autenticacion, almacenamiento seguro y realtime.
- Inventariar APIs existentes y definir la fachada movil.

### Fase 1: MVP de pedidos

- Sesion, contexto, ambientes, mesas, catalogo y orden.
- Cantidades, notas, comensales y cliente predeterminado.
- Envio de comandas y seguimiento de cocina.
- Cola local controlada y reconciliacion.

### Fase 2: operacion comercial

- Seleccion y creacion autorizada de clientes.
- Precuenta e impresion.
- Pago condicionado por configuracion.
- Estado del comprobante y recuperacion de errores, sin bloquear la app esperando Nubefact.

### Fase 3: endurecimiento y despliegue

- Pruebas de carga, concurrencia, seguridad y perdida de red.
- Administracion de dispositivos y telemetria sin datos personales.
- Piloto con un grupo de mozos y despliegue gradual.

## 14. Criterios para seleccionar la tecnologia

La tecnologia elegida debe generar codigo mantenible y permitir:

- consumir APIs REST de Frappe;
- autenticacion OAuth/PKCE;
- almacenamiento cifrado y cola local;
- realtime con reconexion;
- compilaciones reproducibles y firmadas;
- pruebas automatizadas;
- actualizaciones sin depender permanentemente del proveedor del generador.

Si los dispositivos son Android y la operacion sera exclusivamente interna, Android o Flutter constituyen el punto de partida recomendado. Una PWA puede acelerar el piloto, pero debe probarse cuidadosamente en segundo plano, almacenamiento local, alertas y manejo de sesiones.

## 15. Criterios de aceptacion generales

- Un mozo solo ve ambientes y mesas autorizados.
- Abrir una mesa asigna el cliente predeterminado sin mostrar un selector innecesario.
- Precio, impuesto y total coinciden con Restaurant Manage para la misma orden.
- Un doble toque o reintento no duplica platos ni comandas.
- Las notas completas llegan al centro de produccion.
- Dos dispositivos reciben el estado actualizado sin sobrescribirse silenciosamente.
- La perdida y recuperacion de red no pierde una mutacion confirmada ni factura fuera de linea.
- El boton Pagar y la API respetan la configuracion del rol mozo.
- La app no contiene secretos ni permite acceder a otra Company, POS Profile o ambiente.
- El flujo web actual continua funcionando sin regresiones.

