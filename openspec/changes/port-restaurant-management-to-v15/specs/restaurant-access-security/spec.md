## ADDED Requirements

### Requirement: Server-side authorization
Every whitelisted function and document action SHALL authenticate the caller and SHALL validate DocType, document, company, POS Profile, room and ownership permissions appropriate to the operation.

#### Scenario: Authorized restaurant operation
- **WHEN** a user with the required role and room access performs an operation within their company
- **THEN** the server executes the operation and returns only the data required by the client

#### Scenario: Unauthorized direct API call
- **WHEN** a user invokes the same endpoint directly without the required role, company or room access
- **THEN** the server rejects the request without modifying data

#### Scenario: Guest access
- **WHEN** Guest invokes an endpoint that returns POS configuration, orders, workstations, customers, payments or invoices
- **THEN** the server denies access

### Requirement: Safe query construction
All database queries SHALL use the Frappe ORM or bound SQL parameters for client-controlled values, and dynamic field or order expressions MUST be selected from explicit allowlists.

#### Scenario: Malicious input
- **WHEN** an API argument contains SQL syntax, quotes or an unexpected field name
- **THEN** the value is rejected or treated strictly as data and cannot change query structure

#### Scenario: Approved dynamic setting field
- **WHEN** the client requests a setting that is explicitly exposed by the server
- **THEN** the server returns that setting without accepting arbitrary `tabSingles` field access

### Requirement: Company and permission isolation
APIs, lists, kitchen views and reports SHALL restrict records to companies and POS Profiles accessible to the current user.

#### Scenario: User with one company
- **WHEN** a user assigned only to Company A requests sales, payments, orders or kitchen data
- **THEN** no record belonging exclusively to Company B is returned

#### Scenario: Administrator selects a company
- **WHEN** an authorized administrator requests a valid Company B context
- **THEN** results are limited to Company B and the selected context is explicit in the response

### Requirement: Safe browser rendering
The frontend MUST render item names, notes, comments, user names, customer data and identifiers as text or escaped content unless the value originates from a trusted static template.

#### Scenario: Stored markup in an order note
- **WHEN** an order note contains HTML or script-like content
- **THEN** kitchen, popup and order views display it as inert text and do not execute it

### Requirement: Auditable sensitive changes
Changes to waiter assignment, ownership, room access, order state and invoice linkage SHALL preserve the authenticated actor and an auditable document trail.

#### Scenario: Waiter reassignment
- **WHEN** an authorized manager changes the waiter assigned to an order
- **THEN** the business assignment changes through a validated document action while the original creator and audit history remain intact

#### Scenario: Unauthorized owner rewrite
- **WHEN** a caller attempts to update `owner` directly
- **THEN** the server rejects the change
