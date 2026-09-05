# Conservar los totales al consolidar Facturas POS

## Problema

ERPNext consolida las Facturas POS usando importes netos e impuestos ya redondeados por
separado. Cuando la suma de esos componentes difiere por uno o más céntimos del total
cobrado, la Factura de Venta consolidada termina con un total menor y el sistema registra
la diferencia como vuelto o castigo, aunque el cliente no recibió vuelto.

## Solución

En cierres de restaurante, conservar como total objetivo la suma exacta de las Facturas
POS. La diferencia centesimal de cada comprobante se asignará de forma determinista a
una de sus líneas de venta dentro de la consolidada, manteniendo intactos los impuestos,
los pagos y el importe efectivamente cobrado.

## Alcance

- Facturas de Venta y notas de crédito creadas por la consolidación de cierres POS del restaurante.
- Diferencias centesimales originadas por el redondeo separado de neto e impuestos.
- Validación previa al guardado para impedir vuelto o castigo artificial.

## Fuera de alcance

- Modificar Facturas POS ya enviadas.
- Alterar los impuestos calculados o enviados electrónicamente en los comprobantes originales.
- Corregir automáticamente Facturas de Venta consolidadas históricas.
