# Diseño

`POS Closing Entry Detail` conserva el importe de apertura y recibe dos columnas de
auditoría: ventas y gastos. `expected_amount` almacena el saldo neto esperado. El padre
conserva `restaurant_expense_total` como resumen del cierre.

El servidor reconstruye ventas desde las facturas POS incluidas, agrupa gastos enviados
por apertura y método de pago y recalcula siempre desde esos componentes. Esto evita
restar el mismo gasto nuevamente al guardar o refrescar.

Antes de enviar el cierre se buscan gastos en borrador de la apertura. Su existencia
bloquea el envío. Un gasto enviado ya incluido en un cierre tampoco puede cancelarse.

La interfaz consulta el resumen de gastos para mostrar el cálculo antes de guardar,
presenta una advertencia por borradores y ofrece `Ver gastos` con el filtro de apertura.

No se modifican documentos históricos enviados. El reporte obtiene sus gastos mediante
la relación entre `Resto Gastos.pos_opening_entry` y `POS Closing Entry.pos_opening_entry`.
