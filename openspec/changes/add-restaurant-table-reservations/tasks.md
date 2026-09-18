## 1. Modelo y configuración

- [x] 1.1 Crear los DocTypes de reserva y detalle de mesas.
- [x] 1.2 Añadir configuración, serie por empresa y migración de valores iniciales.
- [x] 1.3 Añadir vínculo de reserva en `Table Order` y el rol `resto_reservas`.

## 2. Reglas de negocio

- [x] 2.1 Validar empresa, contacto, periodo, capacidad y mesas duplicadas.
- [x] 2.2 Prevenir cruces concurrentes usando tolerancias configurables.
- [x] 2.3 Implementar transiciones, cancelación y no asistencia auditables.
- [x] 2.4 Implementar check-in idempotente y completar al facturar.

## 3. Experiencia operativa

- [x] 3.1 Añadir botones y filtros del formulario.
- [x] 3.2 Añadir vista calendario/agenda y acceso desde Restaurant Manage.
- [x] 3.3 Mostrar la próxima reserva en las mesas y publicar cambios realtime.

## 4. Seguridad y validación

- [x] 4.1 Configurar permisos por rol y controles de servidor.
- [x] 4.2 Añadir pruebas unitarias de serie, cruces, estados e idempotencia.
- [x] 4.3 Validar OpenSpec, sintaxis, fixtures y Graphify.
