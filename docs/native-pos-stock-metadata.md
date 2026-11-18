# Native POS stock metadata compatibility

ERPNext16.54 and16.60 define POS Invoice.update_stock as Check/default0. A historical restaurant Custom Field with the same name duplicates that native definition and can block fixture synchronization.

The before_migrate helper validates the source/native DocField, column and legacy type before changing metadata. It writes a private snapshot under the current site's WorkIA/native_pos_stock_metadata_compat_v16 (700/600), copies differing supported presentation properties to missing native Property Setters, and removes only duplicate Custom Field metadata through Frappe's bypass API. Existing Property Setters and DocType Layouts remain untouched. Setup skips recreating the Custom Field on a native core.

No invoice values, stock policy, controllers, Company Settings, columns, indexes, accounting or providers are changed. A differing legacy default requires explicit policy review. No global field_order is introduced; insert_after is not a native DocField property, so canonical native order applies unless existing layout/order overrides it.

Pure tests: `python -B -m unittest restaurant_management.setup.test_pos_stock_metadata -v` in a prepared development environment. Native metadata trials require a transaction, rollback, blocked commits/DDL/providers and cache cleanup. This documentation does not authorize running migrations independently.

Recovery evidence contains metadata only. Do not recreate a duplicate field on the native core. Any manual metadata recovery must use the captured state and a reviewed version; invoice/column recovery is outside this fix.

Development validation, 2026-11-18: 18 pure tests passed. A native ORM trial adopted the actual duplicate using six missing Property Setters and one metadata-only deletion. Native field validation, existing setters/layouts, column identity, default0 and 62 invoice states passed; repeated adoption was a no-op. Rollback restored exact metadata and invoice state and the POS cache was cleared. Commits, DDL, business-table writes, queues, email and external network were blocked. Internal metadata realtime notifications were substituted during this trial; notification delivery was not tested. This validates metadata compatibility, not a posted sale or stock movement.
