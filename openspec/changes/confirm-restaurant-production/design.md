## Decision

The form button invokes a small confirmation function instead of calling the existing
async process directly. The dialog identifies the Material Request and warns that the
action creates and submits Work Orders and inventory movements that affect stock.

The confirmation callback invokes the unchanged processing function. Closing or
rejecting the dialog performs no server request, so cancellation has no side effects.

## Rollback

Restore the button callback to process_restaurant_production and remove the confirmation
wrapper. No schema or data migration is involved.
