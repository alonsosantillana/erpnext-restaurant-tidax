## Why

La operacion actual de mozos depende de `Restaurant Manage` en un navegador de escritorio. Aunque el backend ya controla ambientes, mesas, ordenes, comandas, clientes, precios, cocina y pago configurable, falta una interfaz movil deliberadamente disenada para tomar pedidos con rapidez, conectividad variable y controles de dispositivo.

Crear una app separada sin un contrato previo podria duplicar reglas comerciales, exponer APIs demasiado amplias o generar divergencias entre el pedido movil, `Table Order`, cocina y `POS Invoice`.

## Objective

Definir la arquitectura, alcance, seguridad, contratos de integracion y fases de una aplicacion movil para mozos que reutilice `restaurant_management` y mantenga a ERPNext como fuente autoritativa.

## Scope

- App backend: `restaurant_management`.
- Cliente movil por definir segun las capacidades del servidor generador.
- Autenticacion segura de usuarios y dispositivos.
- Acceso a Company, POS Profile, ambientes y mesas permitidos.
- Apertura y consulta de `Table Order`.
- Catalogo, precios, cantidades, notas, comensales y cliente predeterminado.
- Envio de comandas y consulta realtime del estado de cocina.
- Precuenta y pago opcional condicionado por permisos en una fase posterior.
- Idempotencia, concurrencia, reconciliacion y operacion limitada sin conexion.
- Pruebas y despliegue gradual sin afectar `Restaurant Manage`.

## Exclusions

- Implementar el cliente movil dentro de este cambio documental.
- Elegir una tecnologia antes de evaluar el servidor generador.
- Acceso directo del dispositivo a MariaDB.
- Duplicar precios, impuestos o logica de facturacion en la app.
- Facturacion o pagos sin conexion.
- Administracion movil de contabilidad, produccion, inventario o BOM.
- Cambios en SUNAT, Nubefact o reglas tributarias.

## Dependencies and Impact

- Frappe y ERPNext v15.
- `Restaurant Permission`, `Restaurant Company Settings`, `Restaurant Object`, `Table Order` y `Order Entry Item`.
- `Customer`, `POS Profile`, reglas de precios e impuestos de ERPNext.
- Production Center, realtime, impresion, `POS Invoice` y facturacion electronica existentes.
- Plataforma generadora de aplicaciones, cuya documentacion y capacidades aun deben proporcionarse.

El cambio futuro sera de **riesgo medio-alto** porque agregara una superficie API movil, autenticacion persistente, sincronizacion y concurrencia sobre ordenes activas. Esta entrega es solo de documentacion y no modifica comportamiento ni datos.

## Expected Impact

- Un contrato unico impedira que la app replique reglas sensibles.
- Los pedidos moviles ingresaran al mismo flujo de mesas, cocina, caja y auditoria.
- Los reintentos y cortes breves de red no deberan duplicar lineas o comandas.
- La primera entrega movil podra concentrarse en el trabajo del mozo y diferir pago/facturacion hasta calificarlos.

## Acceptance Criteria

- Existe una especificacion funcional y tecnica entregable al proveedor del generador movil.
- El MVP y sus exclusiones estan definidos.
- Se documentan autenticacion, permisos, idempotencia, concurrencia, offline y realtime.
- Se identifican los casos de uso de API sin exponer acceso irrestricto a documentos.
- Se enumeran las capacidades e informacion que debe proporcionar el servidor generador.
- Se define una matriz minima de pruebas y un despliegue por fases.
- No se modifica codigo, metadata, datos ni comportamiento del sistema durante este cambio documental.

