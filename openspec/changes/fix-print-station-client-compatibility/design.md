## Architecture

Add a readiness predicate next to get_restaurant_print_station_controller. It checks
the types of make_id and WebSocketPrinter and the modern prototype methods connect,
reconnect, close, getState, isConnected and submit used by the station. Both pre-load
and post-load guards use the same predicate. Existing loaded controllers retain the
current lifecycle and session identifier behavior.

When incomplete, use the existing frappe.require asset path. If the asset still
does not provide the full contract, throw an operator-readable error describing
the required silent_print update before constructing any printer or controller.
Do not synthesize make_id alone: the legacy printer also lacks lifecycle methods.

## Evidence and Impact

The local Graphify graph identifies Restaurant Print Console and Silent Print
integration. Source review confirms legacy silent_print.js exposes a constructor
without make_id, whereas silent_print_v15.js exports make_id and a class with the
required lifecycle methods. Current startup guards only check the constructor.

Files: restaurant_print_console.js and test_restaurant_print_console.js in the
existing page directory. No changes to DocTypes, hooks, fixtures, server permissions,
other apps, database schema or API signatures.

## Validation

Run Node built-in tests against the actual page script in a VM, with mocked page,
storage and asset loader. Test missing and non-callable make_id, missing lifecycle
methods, legacy-to-modern upgrade, already-ready client, compatible constructor
with stored client ID, load rejection and post-load validation failure. A live
thermal printer and remote server deployment remain outside automated checks.

## Rollback

Revert the frontend predicate/guards and tests. No database or data rollback needed.
