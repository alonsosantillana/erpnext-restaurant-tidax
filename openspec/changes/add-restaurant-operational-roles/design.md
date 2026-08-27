# Design

## Role matrix

| Role | Primary responsibility | Restaurant layout | Orders | Production | POS invoice | Fulfillment |
|---|---|---|---|---|---|---|
| `resto_admin` | Module administration | Manage | Manage | Manage | According to ERPNext permissions | Manage |
| `resto_cajero` | Cashier and payment | Read | Manage | Read | According to ERPNext permissions | Manage |
| `resto_mozo` | Tables and service | Read | Create/update | Read | No implicit grant | Read/update |
| `resto_cocina` | Kitchen production | Read | Read/update production state | Manage production state | No implicit grant | Read |
| `resto_delivery` | Delivery and pickup | Read | Create/update external orders | Read | No implicit grant | Manage |

The restaurant roles grant only app-specific access. Accounting, stock, customer, and POS Invoice access continues to use ERPNext's standard roles and user permissions.

## Method authorization

The generic document method endpoint must not assume every non-read method writes the routed document:

- `Restaurant Object.add_order` requires read access to the object and create access to `Table Order`.
- Production state methods require read access to the Production Center object and write access to `Table Order`.
- Layout methods continue to require write or delete access to `Restaurant Object`.

## Compatibility

Existing role assignments are preserved. A migration patch adds the matching new role to users of `Admin Resto`, `Cajero`, `Mozo`, and `Cocinero`; it does not remove legacy roles.
