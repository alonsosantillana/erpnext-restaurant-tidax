# Design

The right-side order cell contains three vertical regions: the item list, the selected-item editor and the control keypad. Percentage height on the list was unreliable because its direct containing block was a table cell whose used height could grow with its content.

The table cell is a positioned containing block and the `order-side-panel` wrapper is absolutely inset to its visible bounds. This removes the order lines from the table's intrinsic height calculation and provides a definite full-height flex column. The item list uses `flex: 1 1 auto` and `min-height: 0`, allowing it to shrink and scroll. The editor and keypad use fixed flex bases matching their existing heights.

The existing `.panel-order-items` element remains the scroll container, so `TableOrder.scroller()` continues to operate without JavaScript changes.

## Rollback

Remove the wrapper and restore the previous percentage-height rule in `order-items-container.css`.
