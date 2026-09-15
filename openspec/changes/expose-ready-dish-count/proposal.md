# Change: Expose ready dish count to mobile clients

## Why

The mobile table list cannot currently distinguish occupied tables that have dishes waiting for service.

## Objective

Add an aggregate ready quantity to each accessible active-order summary returned by `get_tables`.

## Scope

- Treat `Order Entry Item.status = Completed` as ready.
- Sum item quantities for each active order after the existing access check.
- Extend the OpenAPI contract with `ready_items_count`.

