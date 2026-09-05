# Diseño

El render del plato agregará una clase derivada de `next_status`. Para `Completed` se
usará `production-action-complete`; las demás transiciones conservarán la apariencia
estándar.

La clase de completar define fondo y borde verdes, texto blanco y estados hover/focus
más oscuros. Se mantiene la clase base de Frappe y el comportamiento del evento actual,
por lo que no cambia ninguna llamada al servidor.
