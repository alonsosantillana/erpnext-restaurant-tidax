# restaurant-permission-compatibility Specification

## Purpose

Describe the existing restaurant-permission-compatibility contract reviewed against source revision
8138a20 on 2026-11-13. This is documentation consolidation, not a new feature,
runtime acceptance or deployment authorization. Original decisions and evidence:
[change fix-v16-print-permission-api](../../changes/fix-v16-print-permission-api/).

## Requirements

### Requirement: Compatible silent permission checks
The application SHALL use the native v16 permission API without unsupported arguments and SHALL keep the existing scoped authorization fallbacks silent.

#### Scenario: Native print permission granted
- **WHEN** an authenticated caller has print permission for the POS Invoice
- **THEN** the existing queue request is reached with unchanged company and idempotency parameters

#### Scenario: Scoped restaurant authorization granted
- **WHEN** native permission is denied and the existing linked-order payment authorization allows the caller
- **THEN** printing proceeds without a misleading native denial message

#### Scenario: Access denied
- **WHEN** neither native nor restaurant scoped authorization permits access
- **THEN** a PermissionError is raised and no job is queued

### Requirement: Preserve authentication and electronic authorization
The application SHALL reject Guest before proceeding and SHALL retain the existing write-permission and restaurant fallback checks for electronic processing.

#### Scenario: Unauthenticated caller
- **WHEN** Guest invokes a protected path
- **THEN** AuthenticationError is raised before loading or processing documents

#### Scenario: Electronic access check
- **WHEN** the electronic authorization gate is evaluated
- **THEN** its native or scoped grant decision is preserved without calling a provider during isolated tests

### Requirement: Signature-aware isolated verification
Regression tests SHALL validate the actual native permission signature and SHALL isolate printing and provider side effects.

#### Scenario: Unsupported argument regression
- **WHEN** a permission call uses an argument absent from the real native signature
- **THEN** automated regression verification fails
