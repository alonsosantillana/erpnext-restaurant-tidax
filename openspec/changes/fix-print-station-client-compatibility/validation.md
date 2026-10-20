# Validation

## Automated checks

- Node built-in runner: 8 tests passed against the actual console script in a VM.
- Before the source change: 6 tests failed, including exact reproduction of
  `frappe.silent_print.make_id is not a function`; 2 existing-client cases passed.
- After the change: all 8 passed. Partial-contract cases include each missing
  lifecycle method, missing/non-callable make_id and non-callable constructor.
- JavaScript syntax check and `git diff --check` passed.
- OpenSpec strict validation passed with Node.js 20 before source changes.
- Code-only local Graphify extraction: 3143 nodes, 4796 edges, 350 communities.
  The graph remains ignored by Git.

## Real-client smoke test

Loaded the installed Silent Print v15 asset in a VM starting with a legacy
constructor. Verified that the station requested the modern asset, initialized
the real printer class, retained the generated session client identifier and
left the printer in idle state. No WebSocket, database or physical print jobs
were created.

## Deployment boundary

No other app source was changed. No migrate, build, clear-cache or service restart
was run against a site. The affected server and physical printer were not accessed.

After publishing and deploying the correction, ensure that the server's silent_print
app provides `/assets/silent_print/js/silent_print_v15.js` with make_id and the full
modern connection API. If needed, update that app from its configured repository
and branch, then rebuild assets for silent_print and restaurant_management and
clear the target site's cache. Reload the browser and verify station startup and
a physical test ticket. Operational verification remains pending.
