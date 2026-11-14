## Result — 2026-11-02, America/Lima

Implemented the authorized UI correction in development only. Branch `fix/v16-printer-indicator` from local `version-16` at `4fee22d`. Paired app: silent_print, with its own identically named specification/branch. Both started clean; no existing work was discarded, branches deleted, history rewritten or principal branch merged.

## Diagnosis and implementation

Installed source versions: Frappe16.54.0, ERPNext16.53.0. Both old indicators attempted insertion before .navbar-brand.navbar-home, absent from the v16 Desk. app_ready still fires. The replacement moves one retained SVG control to the visible header in frappe.container.page, with a sidebar fallback; the v15 anchor remains supported. No global multi-host insertion/cloning. Navigation only remounts UI, not bootstrap, master-tab registration or WebSocket initialization.

Existing authorization remains server-controlled. The restaurant link retains /app/restaurant-print-console, new-tab behavior and cache clearing. Only the configured legacy print user gets a master-tab button. Restaurant priority works in both load orders; losing assignment restores only an existing legacy control. A failed refresh remains red across navigation.

## Reproduced failures and checks

- Original paired scripts: initial 20-case offline Chromium suite reproduced 19 failures and one pass (the unauthorized-user case).
- Specialist identified a v15 color regression in the initial candidate: Timeless printer uses fill=var(--icon-stroke), unlike Lucide's stroke. The strengthened v15 glyph fixture reproduced two failures among 22 scenarios. Both controls now set --icon-stroke:currentColor and --icon-fill:none as well as inline stroke/fill.
- Final paired browser suite: **22 passed, zero failures/skips**. Actual scripts execute in isolated Chromium frames with jQuery, v15/v16-shaped hosts, synthetic station data, RPC and WebSocket fixtures. Covers visibility/SVG, hidden cached pages, same-node A/B/A navigation, late hosts, sidebar fallback, 360px narrow headers/hidden sidebar, authorization, both load orders, legacy restoration, one click effect, no mounting RPC/connections, status colors and preserved error state.
- Existing Restaurant Print Console regressions: **8 passed**, zero failures/skips.
- Node syntax checks passed for both production scripts and the new browser suite. git diff --check and strict OpenSpec validation passed in both repos before/after implementation.
- Read-only integration/QA final review approved both diffs after the color fix, without remaining blockers. No specialist edits or external connections.

The browser executable and supporting libraries already existed. Its first launch failed because libasound was not on the default loader path; the test process alone used the existing /tmp/tix-browser-libs/usr/lib/x86_64-linux-gnu directory. Nothing was installed or changed system-wide. Browser documents have restrictive CSP, use local inline source only, forbid fetch/XHR, replace WebSockets and RPCs with fixtures, disable background networking and use no ERP URL. Each run removes only its own mkdtemp profile/HTML directory.

## Reproduction

From the Silent Print repository, with the paired Restaurant Management checkout present:

```bash
PRINT_TEST_CHROMIUM=/path/to/existing/chrome-headless-shell node --test tests/test_print_indicators.cjs
```

Set PRINT_TEST_RESTAURANT_ROOT only when the paired checkout is not a sibling. If needed, scope LD_LIBRARY_PATH to existing browser libraries for that command only. Do not install components, access ERP or open HWB to execute these fixtures. The console regression command from Restaurant Management is:

```bash
node --test restaurant_management/restaurant_management/page/restaurant_print_console/test_restaurant_print_console.js
```

## Boundaries and operational follow-up

No site initialization, database reads/writes, printer connection, print payload, real RPC, invoice, stock or accounting operation. No core, hook, backend API, schema, fixture, patch, permission, operational configuration, service, scheduler or queue changes. No build, migrate, clear-cache, restart, production access or deployment. The existing static asset symlinks point at the development app public directories; reading those links does not prove browser reload or runtime acceptance.

The fixture validates actual browser DOM/CSS behavior, not the complete live Desk stylesheet/session or physical hardware. Separate user-session/HWB acceptance remains pending. For restaurant use, update both apps together in a specifically authorized deployment and hard-reload browser assets; the legacy filename silent_print_v15.js remains intentionally unchanged. A configured station/print user is still required. Opening the console may process pending jobs; it was not opened during this task.

Graphify: queried only the existing Restaurant Management graph, then verified source. No prepared Silent Print graph was found. No graph was generated/installed/configured or versioned; no cross-app graph or remote AI was used. This UI adjustment adds no backend dependency or architectural integration.

README usage and the console route were updated. Source commits are local only. Remote publication, merge and deployment remain separate explicit authorizations. Reversion is to revert only the respective UI commit; no data rollback or migration is required.

## Evidence reconciliation — 2026-11-13

The preceding sections preserve the original delivery state. Later in this
conversation the operator reported "ya ha impreso" and confirmed the indicator
appears in v15.local (the development site's historical name, now running v16).
This is operator-reported physical printing, not a new hardware test by this
documentation refresh. Clearing both pending jobs was not confirmed; no job was
replayed and no all-stations, all-roles or second-server acceptance is inferred.

The user subsequently authorized integrating/pushing both UI commits to
version-16. The delivery recorded successful fast-forward pushes and remote hash
verification for restaurant_management 430dd62 and silent_print 2063fc4. The
restaurant commit is an ancestor of the source revision audited here, 8138a20.
The original local-only/pending-publication statements are historical, not the
current publication status. That authorization did not authorize another
deployment; the separate print-permission correction has its own evidence in
`../fix-v16-print-permission-api/validation.md`.
