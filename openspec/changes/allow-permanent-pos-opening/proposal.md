# Permit explicitly configured permanent restaurant POS openings
## Why
ERPNext v16 rejects an older POS opening when saving a new POS Invoice. An existing restaurant operates a permanent opening; closing it would consolidate historical invoices and exceeds the approved scope.
## What Changes
Add a default-disabled per-company Restaurant Company Settings flag, scoped to its primary POS profile. Extend POS Invoice only through the v16 cooperative class hook. Preserve missing/duplicate, company, submitted status, opening reference and future-date controls. Native validation applies elsewhere.
## Impact
One own app; settings metadata and Python hook. No ERPNext/Frappe core changes, APIs, permission grants, patches, fixtures, financial calculations or historical mutations. High operational risk; explicit user approval received 2026-11-02 for development tests followed by production activation for the affected primary profile only. No site backup requested by user.
## Acceptance
Old valid openings pass only with opt-in and matching primary profile; invalid states fail. No close/reopen, dates changed or historical consolidation. Test in development before production.
