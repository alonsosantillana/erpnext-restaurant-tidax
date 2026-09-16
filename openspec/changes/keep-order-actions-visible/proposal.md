# Change: Keep restaurant order actions visible

## Why

When a table contains many order lines, the item list expands beyond the viewport and pushes the editor, keypad and action buttons out of view.

## Objective

Make the order-item list the only vertically scrollable region in the right panel while keeping the lower order controls visible.

## Scope

- Add an internal layout container to the order side panel.
- Constrain the item list with flex sizing and vertical scrolling.
- Keep the editor and control keypad at their existing fixed heights.
- Preserve existing item selection and automatic scrolling behavior.

## Exclusions

- No changes to order data, pricing, permissions, kitchen statuses or payments.
- No redesign of the order-item cards or action buttons.

## Risk

Low. The change is limited to markup grouping and CSS layout in Restaurant Manage.
