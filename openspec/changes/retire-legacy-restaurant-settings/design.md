## Design

La resolución central `get_restaurant_settings(company)` devuelve exclusivamente
`Restaurant Company Settings`. El Single anterior permanece instalado para permitir
actualizar bases que todavía necesiten ejecutar parches históricos, pero deja de ser
una fuente válida durante la operación.

La impresión de comandas deja de depender de prefijos en la descripción de la mesa.
Después de enviar una orden, el cliente solicita `queue_order_print`; el servidor
determina la empresa desde `Table Order` y usa una ruta `Restaurant Print Route`
de tipo `ORDER`. La ruta es opcional para no cambiar el comportamiento de empresas
que no imprimen comandas desde caja.

Un parche idempotente sustituye los enlaces persistidos del Workspace. Los permisos
del DocType legado se reducen a System Manager para conservar capacidad de soporte
sin exponer una configuración obsoleta al personal operativo.
