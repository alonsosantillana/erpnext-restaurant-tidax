## 1. Especificacion y baseline

- [x] 1.1 Inventariar restos de delivery, dependencias de mesa, campos de direccion y mapeo actual a POS Invoice.
- [x] 1.2 Definir tipos de atencion, separacion de estados, tarifa como Item y limites de Fase 1.
- [x] 1.3 Registrar pruebas de salon actuales que serviran como baseline de regresion.

## 2. Modelo y migracion

- [x] 2.1 Agregar `service_type` a Table Order con `Dine In` predeterminado y reglas condicionales de mesa.
- [x] 2.2 Crear `Restaurant Fulfillment` con enlace unico, instantaneas, canal, pago, estado y auditoria.
- [x] 2.3 Agregar configuracion habilitar delivery/recojo y `delivery_fee_item` a Restaurant Settings.
- [x] 2.4 Implementar patch idempotente para asignar `Dine In` a ordenes existentes sin reinterpretar mesas `D...`.
- [x] 2.5 Validar JSON, permisos, traducciones y carga repetida de metadata.

## 3. Servicios de orden y fulfillment

- [x] 3.1 Crear API autorizada e idempotente para iniciar delivery/recojo sin mesa usando Company y POS Profile activos.
- [x] 3.2 Validar cliente, telefono y relacion Address-Customer; guardar instantaneas sin exponerlas en eventos globales.
- [x] 3.3 Desacoplar datos, items, envio, sincronizacion y eliminacion de Table Order de la presencia obligatoria de `_table`.
- [x] 3.4 Implementar maquina de estados de fulfillment con estado esperado, actor, timestamps y motivo de fallo/cancelacion.
- [x] 3.5 Sincronizar New/Preparing/Ready con el envio y finalizacion de lineas de produccion, incluyendo nuevas rondas.
- [x] 3.6 Agregar o actualizar una unica linea de tarifa mediante el Item configurado y excluirla de produccion.
- [x] 3.7 Publicar eventos after-commit y retornar estado autoritativo para creacion y transiciones.

## 4. Interfaz Restaurant Manage

- [x] 4.1 Agregar navegacion accesible entre Salon, Delivery, Recojo y Production Center.
- [x] 4.2 Crear formulario de nuevo pedido con busqueda/creacion de cliente, telefono, Address, referencia, canal, promesa, tarifa y pago esperado.
- [x] 4.3 Reutilizar selector y administrador de ordenes sin Restaurant Object, ocultando Transferencia, Divide y Comensales cuando no aplican.
- [x] 4.4 Implementar tablero por estados con tarjetas minimizadas, filtros de Company/POS Profile y detalle bajo demanda.
- [x] 4.5 Agregar acciones autorizadas para asignar, despachar, entregar, fallar y cancelar.
- [x] 4.6 Reconciliar dos pantallas en tiempo real, pestañas ocultas y reconexion sin recarga F5.
- [x] 4.7 Serializar altas, cantidades, notas y descuentos antes de enviar, preservando la ultima linea local durante reconciliaciones.
- [x] 4.8 Diferir la reconciliacion realtime mientras existan mutaciones locales y liberar siempre los bloqueos frontend aunque falle el renderizado.
- [x] 4.9 Aplicar color semantico accesible y etiquetas en español a cada etapa operativa del tablero Delivery.
- [x] 4.10 Aplicar la misma identidad visual al tablero de Recojo, incluyendo la etapa terminal Recogido.
- [x] 4.11 Reemplazar los iconos genericos de Pedidos externos, Delivery y Recojo por una familia SVG propia y accesible.
- [x] 4.12 Invalidar el cache local de la pagina Restaurant Manage y versionar los SVG para publicar cambios visuales sin datos obsoletos.

## 5. Production Center

- [x] 5.1 Incluir tipo y etiqueta operativa del pedido en payloads de comandas, consolidacion y atendidos.
- [x] 5.2 Mostrar DELIVERY/RECOJO con orden y cliente, preservando ambiente/mesa para salon.
- [x] 5.3 Excluir el Item de tarifa de centros de produccion.
- [ ] 5.4 Retirar del flujo nuevo la clasificacion por prefijo `D` y documentar los filtros legacy pendientes de limpieza.
- [x] 5.5 Agregar en Comandas un filtro persistente en tiempo real para Todos, Mesas, Entrega a domicilio y Recojo en local.

## 6. Pago, factura e impresion

- [x] 6.1 Mostrar pago anticipado y contra entrega sin considerar el metodo esperado como dinero recibido.
- [ ] 6.2 Bloquear cierre conciliado cuando el cobro contra entrega permanezca pendiente.
- [x] 6.3 Mapear Address y contacto verificados a campos estandar de POS Invoice y mantener la instantanea de fulfillment.
- [ ] 6.4 Verificar que tarifa, impuestos incluidos, descuentos y pagos coincidan entre orden y POS Invoice.
- [ ] 6.5 Incorporar tipo, direccion resumida, telefono y referencia a comandas/precuenta/comprobante solo donde sea necesario y autorizado.
- [x] 6.6 Mantener el momento de emision contra entrega manual hasta recibir validacion funcional/tributaria.

## 7. Seguridad y pruebas automatizadas

- [ ] 7.1 Agregar pruebas unitarias de reglas, estados, idempotencia, tarifa, instantaneas y permisos.
- [ ] 7.2 Agregar pruebas de integracion para delivery/recojo completo, nueva ronda, pago y factura.
- [ ] 7.3 Agregar pruebas negativas para Guest, direccion de otro cliente, otra Company/POS Profile y transiciones concurrentes.
- [x] 7.4 Ejecutar regresion automatizada de salon, cantidades, notas, descuentos, division, transferencia y Production Center.
- [x] 7.5 Validar Python, JavaScript, JSON, OpenSpec y build de assets.

## 8. Calificacion en v15

- [x] 8.1 Ejecutar migrate y pruebas solo en el sitio v15 autorizado, registrando respaldo y versiones.
- [ ] 8.2 Probar manualmente dos navegadores para realtime de tablero y Production Center.
- [ ] 8.3 Probar delivery anticipado, delivery contra entrega, recojo, cancelacion e incidencia.
- [ ] 8.4 Comparar totales e impuestos de orden, tarifa y POS Invoice con fixtures aprobados.
- [x] 8.5 Documentar configuracion, resultados, desviaciones, rollback y decisiones abiertas antes de commit/push.
