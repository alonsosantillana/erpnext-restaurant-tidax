## ADDED Requirements

### Requirement: Installable on supported ERPNext v15
The app SHALL install and migrate on a clean site running a documented supported Frappe/ERPNext v15 version without modifying core apps.

#### Scenario: Clean installation
- **WHEN** an administrator installs the app on a clean supported v15 site with required dependencies
- **THEN** installation and migration complete without missing DocTypes, invalid fixtures or Python import errors

#### Scenario: Repeated migration
- **WHEN** migration is executed again without a version change
- **THEN** hooks and patches remain idempotent and do not delete unrelated metadata or alter business data

### Requirement: Explicit dependency contract
The app MUST declare each required integration and MUST detect optional capabilities without relying on undeclared browser globals or DocTypes.

#### Scenario: Required dependency missing
- **WHEN** installation or startup detects that a required app or compatible version is absent
- **THEN** the system blocks the affected operation with a clear dependency error and does not create partial data

#### Scenario: Printing dependency missing or unavailable
- **WHEN** `silent_print` or WebApp Hardware Bridge is absent or unavailable
- **THEN** the system blocks only the print action with a clear dependency error, preserves any persisted order or invoice, and offers a controlled retry

### Requirement: Self-contained frontend runtime
The app SHALL provide or replace all frontend utilities required by Restaurant Manage, including the functions currently consumed as `frappe.jshtml`, `frappeHelper`, `DeskForm` and related controls.

#### Scenario: Restaurant page loads
- **WHEN** an authorized user opens Restaurant Manage after a successful build
- **THEN** all required assets load in deterministic order without undefined global, missing asset or missing Desk Form errors

#### Scenario: Asset load failure
- **WHEN** a required asset cannot load
- **THEN** the page displays a scoped error, releases its loading state and does not hide or disable the global Desk interface

### Requirement: ERPNext v15 POS initialization
Restaurant Manage SHALL initialize using fields and server methods available in the supported ERPNext v15 version and SHALL NOT query obsolete `POS Settings` fields.

#### Scenario: Valid POS configuration
- **WHEN** an authorized user has a company, accessible POS Profile and required POS opening state
- **THEN** the page loads rooms, settings and POS data successfully

#### Scenario: Incomplete POS configuration
- **WHEN** the user lacks a default company, accessible POS Profile or required opening entry
- **THEN** the page identifies the missing configuration without exposing internal data or leaving the interface blank

### Requirement: Versioned metadata and migrations
Custom Fields, Client Scripts, fixtures and patches owned by the app MUST be versioned, scoped and idempotent.

#### Scenario: Existing metadata from version 1.7.7
- **WHEN** an upgrade encounters existing app-owned metadata
- **THEN** it updates or preserves the metadata without direct destructive SQL and records any required normalization through an idempotent patch

#### Scenario: Unrelated customization exists
- **WHEN** a site contains a Custom Field or Client Script not owned by the app
- **THEN** migration leaves that customization unchanged
