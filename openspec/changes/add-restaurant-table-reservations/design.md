## Design

`Restaurant Reservation` será un documento operativo no submittable. Su estado
representa el flujo `Pending -> Confirmed -> Arrived -> Seated -> Completed`,
con salidas `Cancelled` y `No Show`. Las mesas se almacenarán en el child table
`Restaurant Reservation Table`; exactamente una será la mesa principal.

La serie se resolverá exclusivamente en el servidor desde
`Restaurant Company Settings.reservation_naming_series`. El valor inicial será
`RES-{ABBR}-.YYYY.-.#####`, que genera nombres como `RES-ECS-2026-00001`.

La disponibilidad usará intervalos semiabiertos con preparación y limpieza:
`inicio - preparación < fin existente + limpieza` y
`fin + limpieza > inicio existente - preparación`. Solo `Pending`, `Confirmed`,
`Arrived` y `Seated` bloquean mesas. La validación se repetirá dentro de una
transacción con bloqueo antes de sentar.

La reserva no creará inventario ni orden al registrarse. `Sentar y abrir orden`
usará la mesa principal, el POS Profile y el cliente configurado para crear exactamente
una `Table Order`. El enlace persistido hará la operación idempotente. Al pasar la
orden a `Invoiced`, la reserva se marcará `Completed`.

El tablero de restaurante recibirá un resumen de la siguiente reserva por mesa y
ofrecerá acceso directo a la agenda. Los cambios publicarán un evento realtime; la
autoridad de disponibilidad y transición de estados permanecerá en el servidor.

Los permisos se repartirán así: `resto_admin` administra; `resto_reservas` crea,
confirma, llega, sienta y cancela; `resto_cajero` consulta y sienta; `resto_mozo`
consulta las reservas asignadas y puede sentar cuando tenga acceso a la mesa.
