# Change: Add restaurant operational roles

## Why

The restaurant module currently depends on generic and legacy roles whose permissions do not clearly separate daily operations from restaurant layout configuration. This also causes cashiers to be denied when opening an order because the operation is incorrectly treated as editing a `Restaurant Object`.

## What Changes

- Add five explicit roles: `resto_admin`, `resto_cajero`, `resto_mozo`, `resto_cocina`, and `resto_delivery`.
- Define a least-privilege permission matrix for restaurant configuration, orders, production, payment, and fulfillment.
- Keep legacy roles working and migrate their users to the equivalent new roles.
- Authorize operational document methods by the document they actually create or update instead of requiring restaurant layout write permission.
- Authorize invoice creation using effective `POS Invoice` permissions instead of obsolete Role Profile names.

## Impact

- Affected specs: `restaurant-access-security`
- Affected code: roles and DocType permissions, Restaurant Manage page roles, API document-method authorization, Table Order invoice authorization, migration patches, and tests.
