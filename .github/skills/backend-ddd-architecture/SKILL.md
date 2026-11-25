---
name: backend-ddd-architecture
description: >
  Mandatory stack-neutral Domain-Driven Design and hexagonal architecture
  standard for every backend service, API, worker, or module (Java, Python,
  .NET, Node, or any other stack). Use when creating a backend project,
  adding a bounded context, module, endpoint, use case, persistence adapter,
  or integration, and when reviewing backend structure. Stack skills map
  these layers to their concrete package or project layout.
---

# Backend DDD Architecture

## Mission

Every backend codebase governed by this framework is structured with
Domain-Driven Design and hexagonal (ports and adapters) boundaries. This skill
defines the rules that are identical for every stack. The installed stack
skill defines how those rules map to concrete folders, packages, projects,
and framework mechanisms.

Read [the stack layout contract](./references/stack-layout-contract.md) to find
or validate the stack mapping before creating or moving files.

## Applicability

| Situation | Rule |
| --- | --- |
| New backend project | DDD layout is mandatory from the first commit. |
| New bounded context or module in an existing project | DDD layout is mandatory for the new code. |
| Change inside existing DDD code | Preserve and enforce the layers. |
| Change inside existing non-DDD code | Do not refactor without explicit approval. Keep the change minimal, place new domain logic behind a port when feasible, and report the architectural gap. |
| No stack skill installed for the stack | Apply the neutral layout below with the stack's idiomatic naming, or report `BLOCKED` with the concrete mapping question. |

A client policy may add rules. It cannot remove the dependency rule or the
framework-free domain rule.

## Layers

| Layer | Contains | Must not contain |
| --- | --- | --- |
| `domain` | Entities, value objects, aggregates, domain services, domain events, invariants, domain exceptions, domain-owned ports (for example repository interfaces) | Web, ORM, persistence, messaging, DI-container, serialization, or configuration framework types |
| `application` | Use cases, commands, queries, application services, transaction boundaries, application ports for external capabilities | HTTP models, persistence entities, adapter implementations |
| `infrastructure` | Persistence models and adapters, external service clients, messaging adapters, technical configuration, DI wiring | Business rules or invariants |
| `interfaces` | Inbound adapters: REST/gRPC/GraphQL controllers or routers, CLI handlers, message consumers, request/response DTOs, HTTP validation, API error mapping | Business rules, direct persistence access |

## Dependency Rule

```text
interfaces      -> application -> domain
infrastructure  -> application / domain   (implements ports)
domain          -> nothing outside the domain
```

- Outer layers depend on inner layers, never the reverse.
- Inbound adapters call application use cases only.
- Outbound adapters implement ports declared in `domain` or `application`.
- Wiring happens at the composition root in `infrastructure` or the
  application entry point, never inside `domain`.

## Bounded Contexts

- Derive bounded contexts from business vocabulary and functional
  requirements.
- Do not create a bounded context per OpenAPI tag, controller, endpoint,
  database table, or DTO.
- Each bounded context owns its four layers. Do not share domain models across
  contexts; integrate through application ports, published contracts, or
  anti-corruption adapters.
- Classify each proposed context, aggregate, and invariant as `CONFIRMED`,
  `INFERRED`, or `UNKNOWN`. Do not invent business behavior from type names.

## Modeling Rules

- Aggregates protect their invariants and are modified through their root.
- Value objects are immutable and validate themselves on creation.
- Repositories exist per aggregate root, not per table.
- Domain events describe facts in business language.
- API DTOs, persistence models, and domain objects are distinct types with
  explicit mapping. None of them doubles as another.
- Do not create layers, ports, or abstractions with no current use. DDD
  structure is mandatory; speculative indirection is not.

## Cross-Cutting Governance

- API contracts: follow `openapi-to-ddd` and the approved OpenAPI document.
- Database structure: follow `liquibase-versioning`. Never use ORM automatic
  DDL to create or modify managed schemas.
- Security, evidence states, and scope: follow the global governance and the
  stack skill.

## Validation

When tooling is available, verify the architecture with evidence:

1. No `domain` source imports a web, ORM, persistence, messaging, or
   DI-container framework. Use the stack's architecture test or an import scan.
2. No `interfaces` source imports persistence adapters or ORM repositories.
3. Every outbound adapter implements a declared port.
4. Unit tests for `domain` run without the web framework, database, or
   container.

Report each check as `PASS`, `FAIL`, or `NOT_RUN`. Static inspection alone is
not `VALIDATED`.

## Violations

- Framework annotations, decorators, or base classes in domain types.
- Business logic in controllers, routers, or message handlers.
- Controllers or routers calling ORM repositories or database sessions.
- HTTP DTOs or persistence models used as domain entities.
- Domain services depending on infrastructure.
- A bounded context created per endpoint or table.

## Required Report

1. Applicability case from the table above.
2. Bounded contexts and aggregates with `CONFIRMED`/`INFERRED`/`UNKNOWN`.
3. Layer placement of every created or modified file.
4. Ports and the adapters that implement them.
5. Architecture validation results and `NOT_RUN` checks.
6. Architectural gaps found in existing code and whether refactoring was
   approved.
