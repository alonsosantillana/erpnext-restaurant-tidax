## Why

Mozos vs Platos and Mozos Resumen can currently be restricted only by calendar dates
and waiter. A day may contain several cash sessions, so those filters cannot reproduce
the exact operational population of one submitted POS closing.

## Objective

Allow both waiter reports to be filtered by POS opening and submitted POS closing
without changing their existing result columns.

## What Changes

- Add optional Apertura POS and Cierre POS report filters.
- Restrict link choices by company and restrict closings by the selected opening.
- Apply the filters through POS Invoice session links without duplicating invoice rows.

## Out of Scope

- Changing report columns, totals, waiter attribution, or invoice status rules.
- Changing POS opening or closing documents.
