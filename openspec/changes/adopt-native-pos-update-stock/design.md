# Design

Use a dedicated setup helper from before_migrate and set_custom_fields. Validate ERP source JSON and current standard DocField are Check, the physical column exists and any legacy Custom Field is Check. Snapshot Custom Field, Property Setters and DocType Layouts in private site WorkIA.

Copy meaningful differing DocField properties to missing field Property Setters using types from DocField source metadata; never overwrite an existing setter. Preserve print_hide, no_copy, read_only, in_standard_filter, label/help/default and permission/display attributes. Native default and legacy default are both0.

Remove only the duplicate Custom Field metadata via delete_custom_fields(..., bypass_hooks=True). Do not use delete_doc/on_trash: those delete Property Setters/layout entries. Never invoke updatedb, sql_ddl or mutate POS Invoice rows. Existing DocType field_order setters and layouts stay unchanged; do not create a global field_order or ignored insert_after setter. Native canonical field position applies otherwise.

No patch order dependency: before_migrate runs before sync_fixtures and setup reuses the guard. The setup definition remains as fallback if core source has no native field. Existing stock controllers/Company Settings are untouched.

Recovery: retain exact private metadata snapshot and prior Git revision. Do not recreate the duplicate on a native core. Metadata recovery must be reviewed against the captured state; no automatic data/column rollback or invoice changes.
