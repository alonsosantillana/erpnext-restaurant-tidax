## 1. Baseline and Decisions

- [x] 1.1 Capture the supported Frappe, ERPNext, ovenube_peru and Python version matrix in project documentation.
- [x] 1.2 Produce a file-level comparison of fork 1.7.7, upstream 1.8.6 and ERPNext v15 for runtime, order, POS and helper components.
- [x] 1.3 Inventory every frontend global, external Python import, DocType, Custom Field, Client Script and app dependency used by the fork.
- [x] 1.4 Document `silent_print` and WebApp Hardware Bridge as required printing integrations, with sale persistence and controlled retry on print failure.
- [x] 1.5 Document that MFC-backed production functionality is retained through app-owned DocTypes and the MFC dependency is removed.
- [x] 1.6 Document that `Table Order` remains submittable and is finalized through `submit()`/`cancel()` instead of direct `docstatus` writes.
- [ ] 1.7 Confirm waiter assignment and production states; independent Boleta/Factura and Electronica/Manual fields are approved and `_m` is confirmed as the manual series variant.
- [x] 1.8 Record a baseline of existing security findings and map each finding to a specification requirement and test.

## 2. ERPNext v15 Runtime and Dependencies

- [x] 2.1 Port the minimum reviewed and license-compatible helper assets needed for `frappe.jshtml`, `frappeHelper`, modal and form controls.
- [x] 2.2 Register helper JavaScript and CSS in deterministic order in `hooks.py` and remove duplicate or unused assets.
- [x] 2.3 Add or port the required `Desk Form` metadata and validate loading of every custom restaurant form.
- [x] 2.4 Replace the `POS Settings.is_online` startup check with a supported v15 initialization contract.
- [x] 2.5 Ensure startup errors are scoped to Restaurant Manage and always release loading/freeze state without hiding the global Desk body.
- [ ] 2.6 Centralize supported ERPNext POS method calls in a compatibility adapter and cover their expected response shapes.
- [x] 2.7 Implement a server-side capability/dependency response for electronic invoicing, printing and optional modules.
- [ ] 2.8 Remove or guard residual `posawesome`, `Work Station`, obsolete Material Request and other confirmed dead dependencies.
- [x] 2.9 Update package metadata, README requirements and installation documentation for the supported v15 matrix.
- [x] 2.10 Validate Python imports, JavaScript syntax, JSON metadata and asset paths after the runtime port.
- [x] 2.11 Restore v15 room and table creation by removing request-path debug output, returning persisted state and reconciling the client after commit.
- [x] 2.12 Restore v15 room, table and production-center deletion with callable actions, explicit delete permission and post-commit client reconciliation.
- [x] 2.13 Adapt legacy restaurant item loading to the ERPNext v15 POS parameter and response contract.
- [x] 2.14 Restore item selection by requiring a customer before adding a line and using the v15 POS selector rate while server-side POS Invoice calculation remains authoritative.
- [x] 2.15 Show locally added order lines immediately without depending on realtime reconciliation to release the hidden cart state.
- [x] 2.16 Make quantity, rate, discount, numeric-pad and delete controls update the selected line at the correct time with bounded values and server reconciliation.
- [x] 2.17 Reconcile the locally persisted item state and pending count so the Order action is enabled without depending on realtime delivery.
- [x] 2.18 Publish production-center notifications after commit and reconcile open kitchen views against persisted commands.
- [x] 2.19 Reload persisted production commands whenever a previously opened kitchen view is entered again.
- [x] 2.20 Recalculate the production-center badge from active commands after loading, adding, transitioning or removing kitchen items.
- [x] 2.21 Show unsent order items with a mustard cart and an explicit pending-to-send label until the Order action is completed.
- [x] 2.22 Show each table's total ordered dish quantity while retaining the active-order count for occupancy and permission rules.
- [x] 2.23 Show ordered dishes above each table and keep active diners with configured seating capacity visible below it.
- [x] 2.24 Reconcile source and destination tables idempotently after transfers, with authoritative response data and silent polling fallback.
- [x] 2.25 Reload persisted orders whenever a table is opened and select its active order when the reused manager has no current selection.
- [x] 2.26 Rebuild an order whose button or item container was detached when the table modal DOM was recreated, then reload its dishes.
- [x] 2.27 Display a persistent transfer-mode notice with source order, source table, destination instruction and an explicit cancel action.
- [x] 2.28 Allow the read-only divide template, validate split quantities before mutation and reconcile both resulting accounts immediately.
- [x] 2.29 Initialize divide-account row and account totals from quantity times the tax-inclusive item rate, matching subsequent modal recalculation.
- [x] 2.30 Search the table-order customer Link by customer ID, customer name or tax ID while preserving Customer read permissions.
- [x] 2.31 Preserve complete single-field Link fetch values for waiter names and initialize the Guest Count form from the order's current occupancy on every open.
- [x] 2.32 Add a permission-aware New Customer flow with local duplicate detection, side-effect-free DNI/RUC preview, explicit confirmation, transactional creation and immediate order assignment.
- [x] 2.33 Resolve new customers to a valid leaf Customer Group without mutating the ERP global default, preferring valid global, POS Profile and established customer-type conventions.
- [x] 2.34 Reload the current Table Order from the server before reopening its Customer editor so cached forms always show the latest assigned customer.
- [x] 2.35 Make Guest Count the only guest-count source by removing the duplicate Personas field and migrating waiter-summary metrics to Guest Count without retaining legacy data.
- [x] 2.36 Rename the ambiguous `dinners` field and all related forms, API arguments, counters and reports to `guest_count`, displayed as Numero de comensales.
- [x] 2.37 Remove residual JavaScript references to the former Dinners indicator and payment initializer so tables and payment forms render after the rename.
- [x] 2.38 Include the server-calculated item tax amount in order payloads and apply the push-item response directly so the read-only Tax Amount field never depends on realtime delivery to leave zero.
- [x] 2.39 Restore the global discount action in the order pad with POS Profile permission checks, mutually exclusive amount/percent inputs, immediate total feedback and realtime order reconciliation.
- [x] 2.40 Apply the POS Profile tax-inclusive setting to every loaded invoice tax row so restaurant prices are not taxed twice in order and discount totals.
- [x] 2.41 Route the Account action through an asynchronous, permission-checked print request that validates the pre-account, Silent Print, printer user and master-tab configuration and reports queue success or failure.
- [x] 2.42 Replace legacy kitchen popups with center-scoped Commands, Dish Consolidation and Attended Orders views, atomic command transitions and realtime reconciliation inside Production Center.
- [x] 2.43 Support independent dish transitions alongside whole-command actions and retain/reconcile production updates received while the P3 tab is hidden.
- [x] 2.44 Provide full-day Dish Consolidation and Attended Orders control, including completed quantities without hiding unfinished operational commands from previous days.
- [x] 2.45 Keep mixed-status dishes in their original command card and drive each dish action from its own current status.
- [x] 2.46 Add a progressive mixed-command action that advances only dishes in the earliest pending state.
- [x] 2.47 Add auditable kitchen timestamps, Item-to-Item-Group target fallback, calculated durations, comparable completed-dish averages and compact timing indicators across all Production Center views.
- [x] 2.48 Serialize repeated product selections per order, persist the latest quantity safely and defer command timestamps until Order is pressed.
- [x] 2.49 Preserve the contributing preparation-target source in daily dish consolidation and provide an Escape-aware full-screen Production Center control.

## 3. Security and Data Isolation

- [ ] 3.1 Inventory all whitelisted functions and document methods with caller, role, company, room and document permission requirements.
- [ ] 3.2 Remove guest access from POS configuration and operational data endpoints.
- [ ] 3.3 Add reusable server-side guards for authenticated user, company, POS Profile, room access and order ownership.
- [ ] 3.4 Replace arbitrary `tabSingles` field lookup with an explicit settings allowlist or structured settings API.
- [ ] 3.5 Replace SQL interpolation in page listeners, kitchen utilities, item updates and related code with ORM or bound parameters.
- [ ] 3.6 Protect waiter reassignment and other sensitive mutations with role checks and auditable business fields instead of rewriting `owner`.
- [ ] 3.7 Apply company and permission filters to invoice summary, payment, item, kitchen and order APIs.
- [ ] 3.8 Minimize API response fields and remove unnecessary tax, identity, address and electronic response data.
- [ ] 3.9 Replace unescaped popup and `innerHTML` rendering of order data with safe text or escaped templates.
- [ ] 3.10 Add negative tests for Guest, unauthorized roles, cross-room access, cross-company access, malicious SQL input and stored HTML.

## 4. Order and Kitchen Lifecycle

- [ ] 4.1 Define the canonical Order Entry Item state graph, terminal states and authorized recovery transitions in code.
- [ ] 4.2 Centralize state transition validation and timing updates in one server-side service.
- [ ] 4.3 Correct kitchen/bar filtering, including the overwritten kitchen branch and trusted use of the authenticated user context.
- [ ] 4.4 Replace order-based preparation timing with the approved item/order timing source and test time-zone behavior.
- [ ] 4.5 Fix order deletion so validation occurs before child mutation and sent or later items remain intact.
- [ ] 4.6 Make add, edit, delete, divide and transfer operations atomic and remove internal commits that prevent rollback.
- [x] 4.7 Implement the selected `Table Order` submit/finalization lifecycle without direct `docstatus` updates.
- [ ] 4.8 Add conflict detection for concurrent edits to the same table or order and return reload guidance to the losing client.
- [ ] 4.9 Publish realtime events only after successful persistence and make clients reconcile against server state.
- [ ] 4.10 Replace the destructive daily status rewrite with the approved non-destructive expiry policy or remove the scheduler.
- [ ] 4.11 Add integration tests for create, edit, send, process, complete, split, transfer, waiter change, deletion, rollback and concurrency.
- [x] 4.12 Return persisted order state from creation, reconcile the requesting client and remove the internal waiter-assignment commit.

## 5. POS Invoice and TIDAX/SUNAT Compliance

- [ ] 5.1 Extract invoice preconditions for actor, company, POS Profile, customer identity, items, stock and payments into testable validation functions.
- [ ] 5.2 Replace hardcoded invoice owner, payment mode and operational constants with authenticated context and validated configuration.
- [ ] 5.3 Add explicit Boleta/Factura and Electronica/Manual fields independent of `guest_count`, and model each approved series by company and operating context with clear validation errors. The fields and global series matrix are implemented; company scoping remains.
- [ ] 5.4 Build POS Invoice items, taxes and payments through supported ERPNext v15 APIs and compare calculated totals with approved fixtures.
- [x] 5.5 Make POS Invoice submission and Table Order linkage atomic without direct `docstatus` writes or partial commits.
- [ ] 5.6 Implement and test line discount, global discount, mixed gratuity and total gratuity cases.
- [x] 5.7 Validate the currently approved DNI and RUC identity paths without treating unknown or empty identity as factura by default.
- [ ] 5.8 Make electronic submission idempotent and persist a recoverable state for provider timeout or rejection.
- [ ] 5.9 Ensure electronic invoicing logs and errors exclude credentials and minimize personal/tax data.
- [ ] 5.10 Integrate `silent_print` with WebApp Hardware Bridge for comandas, boletas and facturas, isolating failures from sale completion and supporting retry without duplication.
- [ ] 5.11 Add integration tests for boleta, factura, discounts, gratuity, multiple payments, stock failure, SUNAT success/failure/retry and print failure.
- [ ] 5.12 Obtain functional and tributary approval of before/after invoice fixtures before marking this phase complete.

## 6. Metadata, Fixtures and Reports

- [x] 6.1 Replace malformed fixture declarations with scoped standard fixtures for app-owned Custom Fields and Client Scripts.
- [x] 6.2 Remove destructive SQL from `after_migrate` and move necessary metadata normalization to idempotent code or patches.
- [ ] 6.3 Resolve duplicate `amended_from`, invalid currency options, incomplete select values and external DocType references in app schemas.
- [ ] 6.4 Apply company, date, `docstatus` and permission filters to every restaurant report.
- [ ] 6.5 Correct December/year-boundary and invalid-filter behavior in Productos Vendidos and any equivalent date calculations.
- [ ] 6.6 Remove debug prints, unused imports, dead code and unbounded `SELECT *` within the changed scope.
- [ ] 6.7 Add report tests for multiple companies, cancelled documents, December, empty ranges, invalid filters and representative volume.

## 7. Upgrade and Data Migration

- [ ] 7.1 Define read-only inventory queries for open orders, item states, orphan children, direct docstatus anomalies, invoice links and configuration.
- [ ] 7.2 Run the inventory only on an authorized isolated copy and record anonymized counts without exposing business data.
- [ ] 7.3 Design any required data patches as idempotent operations with preconditions, postconditions and rollback instructions.
- [ ] 7.4 Add automated tests proving each patch is safe on clean, already-migrated and representative legacy states.
- [ ] 7.5 Document backup, restore and reconciliation procedures for upgrade from 1.7.7.

## 8. v15 Qualification

- [x] 8.1 Create an authorized disposable v15 test site and install all required dependencies at documented versions.
- [x] 8.2 Verify clean install, repeated migrate, asset build and app uninstall/reinstall behavior where safe.
- [ ] 8.3 Restore or construct a representative 1.7.7 dataset and execute the upgrade path on a separate disposable site.
- [x] 8.4 Run Python, JavaScript, JSON, hooks, fixtures and OpenSpec validations.
- [ ] 8.5 Run the complete automated app test suite and record versions, commands, duration and results.
- [ ] 8.6 Execute the browser matrix for administrator, manager, cashier, waiter and cook with console and server error monitoring.
- [ ] 8.7 Execute the end-to-end room -> table -> order -> kitchen -> payment -> POS Invoice -> electronic submission -> print flow.
- [ ] 8.8 Execute cross-company, permission, rollback, concurrency and dependency-failure scenarios.
- [ ] 8.9 Measure representative kitchen endpoint and report performance and record any accepted thresholds or follow-up work.

## 9. Documentation and Closure

- [ ] 9.1 Update README with supported versions, dependency matrix, installation, configuration and known limitations.
- [ ] 9.2 Document administrator configuration for rooms, permissions, POS Profiles, series, electronic invoicing and printing.
- [ ] 9.3 Record all implementation deviations and link them to approved OpenSpec updates.
- [ ] 9.4 Record test evidence, unresolved risks, rollback readiness and required operational approvals in the change.
- [ ] 9.5 Review `git diff` for secrets, generated artifacts, unrelated changes and accidental core modifications.
- [ ] 9.6 Confirm all acceptance criteria and OpenSpec tasks are satisfied before proposing archive, commit, push or deployment.
