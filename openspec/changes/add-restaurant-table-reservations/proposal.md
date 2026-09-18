## Why

El restaurante necesita reservar una o varias mesas antes de crear una orden, evitar
cruces de horario y convertir la reserva en atención real cuando llega el cliente.
Actualmente las mesas solo reflejan órdenes activas y no existe una agenda operativa.

## Objective

Incorporar un flujo auditable de reservas por empresa que controle disponibilidad,
capacidad, llegada, asignación de mesa y apertura idempotente de la orden de atención.

## What Changes

- Crear `Restaurant Reservation` y su detalle de mesas.
- Numerar cada reserva con la abreviatura de la empresa, por ejemplo
  `RES-ECS-2026-00001`.
- Añadir configuración de reservas por empresa: activación, serie, duración,
  tolerancias y cliente predeterminado.
- Validar capacidad, empresa, horarios y cruces de mesas en el servidor.
- Añadir acciones Confirmar, Registrar llegada, Sentar y abrir orden, No asistió y
  Cancelar.
- Mostrar las reservas en agenda/calendario y exponerlas desde Restaurant Manage.
- Vincular la reserva con una sola `Table Order` y completar la reserva al facturar.
- Incorporar el rol `resto_reservas` y permisos mínimos para caja, mozo y reservas.

## Exclusions

- Cobros anticipados o garantías.
- Mensajería automática por WhatsApp, SMS o correo.
- Reservas públicas desde un portal externo.
- Renombrar documentos históricos.

## Acceptance Criteria

- Dos empresas nunca comparten la numeración de reservas.
- Una mesa no puede reservarse para intervalos activos que se crucen.
- Repetir la acción de sentar no crea una segunda orden.
- Canceladas, completadas y no asistidas dejan de bloquear disponibilidad.
- La agenda y Restaurant Manage se actualizan después de cada cambio relevante.
