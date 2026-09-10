## 1. Descubrimiento y decisiones

- [x] 1.1 Documentar objetivo, alcance del MVP, exclusiones y flujo del mozo.
- [x] 1.2 Revisar con Graphify y codigo los limites actuales de Restaurant Manage, Table Order y API.
- [ ] 1.3 Recibir documentacion, version, licenciamiento y metodo de entrega del servidor generador.
- [ ] 1.4 Definir Android/iOS/PWA, dispositivos minimos, conectividad y distribucion.
- [ ] 1.5 Ejecutar una prueba tecnica firmada del generador con OAuth/PKCE, almacenamiento seguro y realtime.

## 2. Contrato backend

- [ ] 2.1 Inventariar y clasificar APIs actuales que puedan reutilizarse sin exponer metodos genericos.
- [ ] 2.2 Definir OpenAPI versionada para contexto, mesas, catalogo, orden, lineas, cocina y sincronizacion.
- [ ] 2.3 Especificar codigos de error, capacidades, paginacion, versiones e idempotencia.
- [ ] 2.4 Decidir persistencia y caducidad de dispositivos y claves idempotentes.
- [ ] 2.5 Crear un OpenSpec de implementacion antes de modificar API, DocTypes, hooks o permisos.

## 3. Seguridad

- [ ] 3.1 Configurar dominio HTTPS y OAuth 2.0 con PKCE en un ambiente aislado.
- [ ] 3.2 Implementar revocacion, almacenamiento seguro y expiracion de sesiones.
- [ ] 3.3 Validar Company, POS Profile, ambiente, mesa y capacidades en cada endpoint.
- [ ] 3.4 Definir minimizacion, cifrado y eliminacion de cache local.
- [ ] 3.5 Ejecutar pruebas negativas, limites de tasa y revision de secretos.

## 4. MVP movil

- [ ] 4.1 Implementar sesion, contexto, ambientes y mesas.
- [ ] 4.2 Implementar catalogo paginado y precios autoritativos.
- [ ] 4.3 Implementar apertura/recuperacion de orden, cliente predeterminado y comensales.
- [ ] 4.4 Implementar cantidades, notas y eliminacion permitida.
- [ ] 4.5 Implementar confirmacion y envio idempotente a cocina.
- [ ] 4.6 Implementar estados de preparacion y reconciliacion realtime.
- [ ] 4.7 Implementar cache y cola local limitada con conflictos visibles.

## 5. Fase comercial

- [ ] 5.1 Implementar seleccion/creacion autorizada de cliente.
- [ ] 5.2 Implementar solicitud de precuenta e impresion acordada.
- [ ] 5.3 Implementar pago solo con capacidad de rol y conexion confirmada.
- [ ] 5.4 Mostrar POS Invoice y estado electronico sin bloquear indefinidamente la interfaz.

## 6. Validacion y despliegue

- [ ] 6.1 Ejecutar pruebas unitarias y de integracion del backend.
- [ ] 6.2 Probar doble toque, concurrencia, perdida de red y dos dispositivos.
- [ ] 6.3 Comparar productos, precios, impuestos y totales con Restaurant Manage.
- [ ] 6.4 Ejecutar regresion de comandas, P3/P5, precuenta, caja y facturacion.
- [ ] 6.5 Ejecutar piloto controlado, documentar incidencias y desplegar gradualmente.

