# Restaurant order panel

## ADDED Requirements

### Requirement: Long orders preserve access to order actions

The Restaurant Manage order panel SHALL constrain the list of ordered items to the available vertical space and SHALL keep the editor, keypad and action buttons visible.

#### Scenario: Order contains more items than fit in the viewport

- **GIVEN** an open table order contains more item rows than fit in the available right panel
- **WHEN** the order is displayed
- **THEN** the item list provides vertical scrolling
- **AND** the lower editor, keypad and action buttons remain visible

#### Scenario: Selected item is outside the visible list area

- **GIVEN** a long order with an item outside the current scroll position
- **WHEN** the application selects that item
- **THEN** the existing item scroller moves the item-list region without moving the lower controls
