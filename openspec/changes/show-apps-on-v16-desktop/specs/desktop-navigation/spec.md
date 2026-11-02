## ADDED Requirements

### Requirement: Installed app discovery follows existing access
The app SHALL declare a Frappe v16 Apps entry and app-owned standard Dock targeting the existing Workspace `Restaurant Management` at `/desk/restaurant-management`, without granting permissions.

#### Scenario: Authorized System User
- **WHEN** an authorized System User opens Apps in a site with this app and its target installed
- **THEN** the app entry and effective Dock lead to the existing target using native access checks

#### Scenario: User or target is ineligible
- **WHEN** the session is Guest or Website User, the app/target is absent, the relevant module is blocked or native target access is denied
- **THEN** the callback returns false and boot exposes no usable app route or Dock

### Requirement: Activation preserves existing behavior
The change SHALL be applied only to development as targeted standard navigation metadata and SHALL preserve official apps, personal navigation, financial logic and concurrent work.

#### Scenario: Repeated targeted import
- **WHEN** the same Dock JSON is imported twice
- **THEN** only one standard Dock exists for this app and existing site/user layers and unrelated data are unchanged

#### Scenario: Rollback or conflicting metadata
- **WHEN** a reserved Dock name is owned by unrelated or non-standard metadata
- **THEN** application stops without overwriting it and the prior code remains recoverable
