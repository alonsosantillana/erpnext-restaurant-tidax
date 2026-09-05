# Integrar gastos al cierre POS

## Problema

El cierre estándar calcula el saldo esperado como fondo inicial más cobros, pero no
descuenta los egresos operativos registrados durante esa misma apertura. El cajero
termina conciliando contra un importe superior al efectivo o saldo realmente disponible.

## Solución

Vincular los gastos enviados por `POS Opening Entry` y `Mode of Payment`, mostrarlos
en la conciliación y calcular `Esperado = Apertura + Ventas - Gastos`. Los gastos no
modifican ventas, impuestos ni comprobantes fiscales.

## Alcance

- Cierres nuevos de todas las empresas configuradas.
- Gastos enviados de la apertura seleccionada.
- Bloqueo por gastos en borrador.
- Reporte de cierre relacionado por apertura, no solamente por fecha.
- Resumen enviado reconstruido con el cierre actualmente abierto, sin reutilizar HTML de otro cierre.
- Ventas por método de pago mostradas antes de descontar gastos operativos.

## Fuera de alcance

- Crear asientos contables nuevos desde `Resto Gastos`.
- Reescribir cierres POS históricos enviados.
