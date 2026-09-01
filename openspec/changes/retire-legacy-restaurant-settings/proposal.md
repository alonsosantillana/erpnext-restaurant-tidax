## Why

`Restaurant Company Settings` ya es la configuración efectiva por empresa, pero el
Workspace y algunos flujos conservan referencias a `Restaurant Settings`. Esto deja
dos interfaces para la misma finalidad y mantiene reglas de impresión obsoletas.

## Objective

Usar `Restaurant Company Settings` como única fuente de configuración en ejecución,
retirar la navegación y los campos heredados, y conservar el DocType anterior solo
como compatibilidad de actualización.

## What Changes

- Reemplazar los enlaces del Workspace por `Restaurant Company Settings`.
- Eliminar el fallback en ejecución hacia el Single `Restaurant Settings`.
- Quitar `Legacy Print Routing` y sus campos de prefijos de mesa.
- Enviar la impresión de comandas mediante la ruta moderna `ORDER`, cuando exista.
- Ocultar el DocType legado a usuarios operativos sin borrar datos históricos.

## Acceptance Criteria

- Los flujos del restaurante resuelven únicamente configuración por empresa.
- El Workspace no enlaza a `Restaurant Settings`.
- `Restaurant Company Settings` no muestra campos de impresión heredados.
- Una ruta `ORDER` ausente o deshabilitada no bloquea el envío de la comanda.
- La separación multiempresa se conserva.
