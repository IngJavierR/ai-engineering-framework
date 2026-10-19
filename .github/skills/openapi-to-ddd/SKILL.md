
---
name: openapi-to-ddd
description: >
  Analyze and implement Java Spring Boot REST APIs
  from OpenAPI contracts using Domain-Driven Design
  and hexagonal architecture. Use for new projects,
  new endpoints, existing API extensions, contract
  compatibility analysis, and contract test planning.
  Coordinate database structural changes through
  Liquibase XML governance.
---

# OpenAPI to DDD

## Mission

Build or evolve Java APIs using an approved OpenAPI
contract and a maintainable DDD architecture.

Support:
- NEW_PROJECT
- EXISTING_PROJECT
- NEW_ENDPOINT
- EXTEND_API
- MODIFY_API_CONTRACT

Do not treat OpenAPI paths as bounded contexts.

## Mandatory Instructions

Follow repository and project instructions:
- Java engineering standards
- OpenAPI and DDD governance
- Liquibase structural governance
- Applicable client policies

Read references:
- references/ddd-structure.md
- references/contract-compatibility.md

If structural database changes are required,
use the liquibase-versioning skill when available.

If it is unavailable, report the dependency
and do not bypass Liquibase XML requirements.

## Workflow

### 1. Discover Inputs

Identify:
- OpenAPI document and specification version
- Functional requirements
- Acceptance criteria and test cases
- New or existing project
- Java and Spring Boot versions
- Existing architecture, when available
- Approved project and client policies

Do not invent missing business rules.

### 2. Validate OpenAPI

Analyze:
- Syntax and reference resolution
- Paths and HTTP methods
- Operation identifiers
- Request and response schemas
- Required and optional properties
- Status codes
- Headers and media types
- Security schemes and requirements
- Validation constraints
- Error response contracts

Never silently modify the approved contract.

Report invalid or ambiguous definitions.

### 3. Analyze Existing Project

For existing projects:
- Inspect repository modules and packages.
- Identify controllers and use cases.
- Discover existing aggregates and value objects.
- Identify persistence adapters.
- Locate existing tests and OpenAPI contracts.
- Identify existing database changelogs.
- Preserve architectural conventions.

Create a change impact analysis before coding.

### 4. Identify Domain Concepts

From the contract AND functional requirements:

- Propose relevant bounded contexts.
- Identify entities and value objects.
- Identify potential aggregates.
- Describe domain invariants.
- Identify application use cases.
- Identify persistence and integration ports.

Distinguish:
- CONFIRMED: supported by requirements.
- INFERRED: reasonable assumption.
- UNKNOWN: requires clarification.

Do not invent domain behavior from DTO names.

### 5. Design Architecture

Use the approved project architecture.

For a new Java Spring Boot project, the default
reference architecture is DDD with hexagonal
boundaries.

Separate:
- Domain
- Application
- Infrastructure
- API interfaces

Do not expose persistence entities as API DTOs.

Keep the domain independent from:
- Spring
- HTTP
- JPA
- Database-specific implementations

### 6. Plan Changes

Produce:
- New or modified API operations.
- Domain components.
- Application use cases.
- Required adapters.
- Database structural changes.
- Files to create or update.
- Existing functionality to preserve.
- Required tests.

For existing projects, define an allowed
change scope.

Do not modify unrelated modules.

### 7. Database Governance

When structural database changes are required:
- Use Liquibase XML.
- Create new changesets.
- Preserve previously executed changesets.
- Update the root changelog as required.
- Evaluate data preservation and compatibility.
- Never use Hibernate automatic DDL.

Do not generate uncontrolled DDL scripts.

### 8. Contract Tests

Plan tests to verify:
- Every required HTTP operation.
- HTTP status codes.
- Request schema validation.
- Response schema validation.
- Required and optional fields.
- Error contracts.
- Authentication and authorization behavior.
- Backward compatibility, when relevant.

Use supplied acceptance criteria.

Do not infer functional success solely
from generated controller compilation.

### 9. Compatibility Analysis

For existing APIs:
- Compare the proposed contract with the baseline.
- Identify removed or changed operations.
- Detect changed required fields.
- Evaluate response schema changes.
- Evaluate error and security contract changes.
- Detect possible consumer incompatibilities.

Read references/contract-compatibility.md.

Do not declare compatibility without evidence.

### 10. Execution and Validation

When implementation is authorized and
tooling is available:
- Implement the approved scope.
- Compile the project.
- Run unit tests.
- Run integration tests.
- Run contract tests.
- Validate Liquibase if database changes exist.
- Report regression results.

Never claim that a check passed if it was
not executed.

### 11. Documentation

Document:
- Contract decisions.
- Domain boundaries.
- Architectural assumptions.
- Changes to existing components.
- Database structural modifications.
- Test coverage and results.
- Known limitations.

Update README when setup, architecture,
configuration, or usage changes.

## Required Report

1. Request classification
2. OpenAPI contract analysis
3. Domain model proposal
4. Architecture proposal
5. Change impact analysis
6. Database structural requirements
7. Contract and regression test plan
8. Compatibility assessment
9. Validation evidence
10. Final status

## Status

Use one of:
- ANALYZED
- READY_FOR_IMPLEMENTATION
- READY_FOR_VALIDATION
- VALIDATED
- BLOCKED

Use VALIDATED only after all mandatory
applicable validations pass.

## Restrictions

- No unrelated functionality changes.
- No unauthorized breaking API changes.
- No invented business requirements.
- No uncontrolled structural DDL.
- No modification of applied changesets.
- No fabricated test results.
- No unapproved destructive operations.
