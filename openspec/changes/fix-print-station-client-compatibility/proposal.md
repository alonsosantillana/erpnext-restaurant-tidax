## Why

Print station startup currently accepts any truthy WebSocketPrinter, including the
legacy Silent Print client. That implementation lacks make_id and the connection
lifecycle API required by the station, causing startup to fail with a TypeError.

## Objective

Require the complete modern browser client before constructing a print station.

## What Changes

- Check callable make_id and WebSocketPrinter plus required prototype methods.
- Load the existing silent_print_v15.js asset when the current client is incomplete.
- Reject an unavailable/incomplete client with an actionable update message.
- Test old, partial, modern and failed client loading in Node without real printers.

## Scope and Risk

Only Restaurant Print Console frontend startup and its tests are affected.
No hooks, schemas, APIs, routes, fixtures, jobs, server leases or Silent Print app
files are changed. Low-impact frontend compatibility fix; no production restart.

## Acceptance Criteria

- A legacy client triggers modern client loading before station construction.
- A complete modern client starts without an unnecessary asset request.
- An incompatible client cannot create a station controller or printer connection.
- The failure tells the operator to update Silent Print and reload the page.

## Exclusions

No changes to printer drivers, Hardware Bridge protocols or accounting workflows.
