# Validation

## Automated checks

- `openspec validate add-restaurant-operational-roles --strict`: passed.
- Python compilation for the modified API, patch, controllers, and tests: passed.
- JSON parsing for affected DocTypes, pages, reports, dashboard charts, and fixtures: passed.
- `Table Order` test module: 32 tests passed.
- `Restaurant Object` test module: 28 tests passed.
- `Restaurant Company Settings` test module: 4 tests passed.

## Site verification

- Migrated `v15.local` successfully.
- Confirmed all five `resto_*` roles exist.
- Confirmed `cajero.erpcloud@tidax.pe` received `resto_cajero` from its legacy `Cajero` assignment.
- Confirmed the cashier can read an ERPCLOUD table and create `Table Order` while direct `Restaurant Object` create and write remain denied.
- Exercised `Restaurant Object.add_order` through the real API authorization path with its mutation mocked; authorization succeeded.

## Environment note

The DocType-wide test command was blocked during unrelated ERPNext test-record setup because the site lacks `All Supplier Groups`. The three relevant test modules were therefore executed directly and all passed.
