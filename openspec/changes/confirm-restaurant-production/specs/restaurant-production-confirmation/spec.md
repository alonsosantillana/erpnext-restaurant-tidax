## ADDED Requirements

### Requirement: Fast production requires explicit confirmation

The Material Request form SHALL request confirmation before executing restaurant
production from the Procesar producción button.

#### Scenario: User accepts production

- **GIVEN** a submitted restaurant Material Request exposes Procesar producción
- **WHEN** the user presses the button and confirms the warning
- **THEN** the existing production server operation is invoked exactly once
- **AND** the dialog states that Work Orders and inventory movements will be submitted

#### Scenario: User cancels production

- **GIVEN** the confirmation dialog is open
- **WHEN** the user cancels or closes it
- **THEN** no production server operation is invoked
- **AND** no Work Order or inventory movement is created by that interaction
