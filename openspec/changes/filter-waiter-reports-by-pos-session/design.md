## Decision

Both reports keep their existing date and waiter filters. Apertura POS and Cierre POS
are optional additional constraints.

The server matches an opening first through POS Invoice.restaurant_pos_opening_entry
and falls back to the submitted POS Closing Entry reference for legacy invoices. It
matches a closing through POS Invoice Reference and requires the closing to be
submitted. EXISTS predicates avoid multiplying invoices or item quantities.

The Cierre POS selector is scoped by company and, when present, the selected Apertura
POS. Report columns and aggregation formulas remain unchanged.

## Rollback

Remove the two client filters and the shared POS-session SQL helper calls. No schema or
business data migration is involved.
