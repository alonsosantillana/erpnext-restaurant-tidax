# Adopt native POS update_stock metadata

## Problem
Restaurant setup defines a Custom Field named POS Invoice.update_stock although ERPNext16.54 and16.60 already define the same Check/default0 field. A legacy duplicate blocks fixture validation during migrate.

## Scope
Adopt the existing standard field before fixture synchronization; preserve existing field properties/Property Setters/DocType Layouts and prevent setup from recreating the duplicate. Keep the existing column and all invoice values, stock policy and accounting unchanged. No DDL, invoice writes, recalculation, providers, backups or production code edits.

## Acceptance
Exactly one standard field remains; legacy presentation flags transfer with native Property Setter types and existing overrides win; metadata-only removal uses Frappe bypass API. Guard incompatible types/absent column before mutation. Repeat runs cause no extra writes. Pure tests and a rollback-only development metadata trial precede publication.

## Risk
High metadata/migration scope on an inventory flag. No financial behavior change intended; fail closed on incompatible state.
