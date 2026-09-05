## Why

Procesar producción currently starts immediately and creates submitted manufacturing
and inventory documents. An accidental click can therefore affect stock before the
user has a chance to review the action.

## Objective

Require explicit user confirmation immediately before processing restaurant production.

## What Changes

- Route the Procesar producción button through a confirmation dialog.
- Explain that Work Orders and stock movements will be created and submitted.
- Call the existing server process only after confirmation.

## Out of Scope

- Changing production calculations, permissions, dates, or server-side processing.
