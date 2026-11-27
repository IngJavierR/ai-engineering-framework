---
name: openapi-to-ddd
description: >
  Analyze and implement backend REST APIs in any
  stack from OpenAPI contracts using Domain-Driven Design
  and hexagonal architecture. Use for new projects,
  new endpoints, existing API extensions, contract
  compatibility analysis, and contract test planning.
  Coordinate database structural changes through
  Liquibase XML governance.
---

# OpenAPI to DDD

## Mission

Build or evolve backend REST APIs using an approved OpenAPI
contract and the consumer's approved architecture.

Support:
- NEW_PROJECT
- EXISTING_PROJECT
- NEW_ENDPOINT
- EXTEND_API
- MODIFY_API_CONTRACT

Do not treat OpenAPI paths as bounded contexts.

## Mandatory Instructions

Follow repository and project instructions:
- `backend-ddd-architecture` (mandatory for every backend stack)
- The installed stack skill, for example `java-spring-development` or
  `fastapi-development`, and its `references/ddd-layout.md`
- OpenAPI and DDD governance
- Liquibase structural governance
- Applicable client policies

Read `references/contract-compatibility.md`. For a stack without a registered
layout, apply the neutral layers from `backend-ddd-architecture` or report
`BLOCKED` with the concrete mapping question.

If structural database changes are required,
use the liquibase-versioning skill when available.

If it is unavailable, report the dependency
and do not bypass Liquibase XML requirements.

## Workflow

### 1. Discover Inputs

Identify:
- `backend.input.yaml` and its approved OpenAPI and `test-cases.yaml` inputs.
- OpenAPI document and specification version
- Functional requirements
- Acceptance criteria and test cases
- New or existing project
- Backend stack, language and framework versions
- Existing architecture, when available
- Approved project and client policies

Do not invent missing business rules.

Run `tools/validate_backend_contracts.py --input backend.input.yaml` before
implementation. Without a `VALID` result, an approved contract, or declared
test cases, report `BLOCKED` unless a client policy explicitly grants an
exception.

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

Document whether the selected validator covers the OpenAPI constructs
used by the contract. Parsing YAML or resolving references validates
the document input; it does not validate runtime HTTP conformance.

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

Apply `backend-ddd-architecture`. DDD with hexagonal boundaries is mandatory
for new backend projects and new bounded contexts in every stack. Existing
non-DDD code is not refactored without approval; report the gap.

Separate:
- Domain
- Application
- Infrastructure
- Interfaces (inbound adapters)

Place files according to the stack skill's `references/ddd-layout.md`.

Do not expose persistence entities as API DTOs.

Keep the domain independent from:
- Web frameworks and HTTP
- ORM and persistence frameworks
- Dependency-injection containers
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
- Never use ORM or automatic DDL, including Hibernate `ddl-auto`, SQLAlchemy
  `create_all`, applied Alembic `autogenerate`, EF `EnsureCreated`, Prisma
  `db push`, TypeORM `synchronize`, or Sequelize `sync`.

Do not generate uncontrolled DDL scripts.

### 8. Test Plan — All Layers

Read `references/backend-unit-testing.md` before writing any test. Every
`TC-*` case declared in `test-cases.yaml` must be verified at each layer
that independently enforces part of the scenario:

- **Domain** — invariants, aggregate construction rules, domain errors.
  No web framework, ORM, or database import allowed.
- **Application** — use-case orchestration with fake ports. No real store.
- **Infrastructure** — persistence and adapter behavior against a
  disposable, isolated store. No web app.
- **Interfaces** — HTTP status, response schema, validation errors, error
  contract. In-process app with fake application dependencies.

For each applicable validation mechanism, include negative cases for:
- required properties
- property types
- formats
- lengths and other declared constraints
- `additionalProperties` behavior when defined by the contract

Document unsupported constructs and validation limitations. Do not
present a partial validator as complete OpenAPI conformance.

Validate real HTTP requests and responses against the approved contract.

Use supplied acceptance criteria.

Implement every case declared in `test-cases.yaml`, report its ID, and
record the result per layer following the evidence template in
`references/backend-unit-testing.md`. Read `references/backend-test-cases.md`
for case design guidance.

Do not infer functional success solely from generated controller compilation.

### 9. Compatibility Analysis

For existing APIs:
- Compare the proposed contract with the baseline.
- Identify removed or changed operations.
- Detect changed required fields.
- Evaluate response schema changes.
- Evaluate error and security contract changes.
- Detect possible consumer incompatibilities.

Analyze compatibility separately for:
- existing requests sent to the proposed API
- proposed requests sent to the existing API when rollout requires it
- existing consumers interpreting proposed responses
- strict consumers that reject unknown response properties

Distinguish optional properties from omission, JSON nullability and
persistence nullability. They have different compatibility effects.

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
- Run the declared Gatling `smoke` profile when performance is required.
- Report regression results.

Use the declared consumer commands. At minimum, evidence must distinguish:

| Validation | Java Spring | Python FastAPI | Generic |
| --- | --- | --- | --- |
| Compile/types | `mvn -q -DskipTests compile` | `ruff`/`mypy` if present | Consumer command |
| Unit/integration | `mvn test` | `pytest` | Consumer command |
| Runtime contract | Request/response validator | `schemathesis`/`openapi-core` | Declared tool |
| Generated compatibility | springdoc `/v3/api-docs` | `app.openapi()` | `/openapi.json` |
| Liquibase | Maven `validate` + disposable `update` | CLI/Docker equivalent | CLI/Docker equivalent |
| Gatling | `mvn gatling:test` | `performance/gatling` `./mvnw gatling:test` | Same as Python |

Use evidence states consistently:
- GENERATED: artifacts were produced; compilation is not implied.
- COMPILED: compilation succeeded with evidence.
- TESTED: tests ran with verifiable results and known scope.
- VALIDATED: declared acceptance criteria have sufficient evidence.

Report NOT_RUN for applicable checks that were not performed. Do not
use VALIDATED for generated artifacts, static inspection, or tests
whose scope does not satisfy the declared acceptance criteria.

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

For validation evidence, report the evidence state, checks executed,
checks NOT_RUN, scope, limitations and supporting artifacts.

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
