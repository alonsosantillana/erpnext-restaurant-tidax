# Diseño

La app sobrescribe la clase de `POS Invoice Merge Log`, sin modificar ERPNext core. Después
del mapeo estándar y antes de guardar la Factura de Venta, calcula por cada Factura POS:

`residuo = total del comprobante - neto - impuestos posteriores al descuento`

El residuo se redondea con la precisión de moneda. Si es distinto de cero, se incorpora a
la última línea elegible que proviene de ese comprobante. Se ajustan importe y tarifa en
moneda de transacción y moneda base. Los impuestos agregados se conservan exactamente como
los entregó el mapeo estándar.

La conciliación solo se activa cuando las facturas pertenecen a un Perfil POS configurado
en `Restaurant Company Settings`. Para evitar ocultar errores distintos del redondeo, cada
residuo debe ser menor o igual a un céntimo por comprobante; una diferencia mayor bloquea
la consolidación con un mensaje de diagnóstico.

Antes de devolver el documento se limpian `change_amount` y `write_off_amount`. El guardado
estándar recalcula la factura con el total ya conciliado, por lo que pago, total y saldo
coinciden sin usar una cuenta de redondeo.
