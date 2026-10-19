
# Java DDD Architecture Reference

## Purpose

Define the default DDD architecture for new
Java Spring Boot APIs.

Existing projects must preserve their approved
architecture unless change is authorized.

## Default Package Structure

com.company.context/
  domain/
    model/
    event/
    service/
    port/
  application/
    usecase/
    command/
    query/
    port/
  infrastructure/
    persistence/
    integration/
    configuration/
  interfaces/
    rest/
      dto/
      mapper/

## Domain Layer

Contains:
- Entities
- Value objects
- Aggregates
- Domain services
- Domain events
- Business invariants

Rules:
- No Spring annotations.
- No JPA annotations.
- No HTTP dependencies.
- No infrastructure dependencies.
- Protect domain invariants.

## Application Layer

Contains:
- Use cases
- Application orchestration
- Commands and queries
- Ports for external capabilities

Rules:
- Coordinates domain operations.
- Does not contain HTTP-specific models.
- Does not depend on infrastructure adapters.

## Infrastructure Layer

Contains:
- JPA entities
- Persistence adapters
- External service clients
- Technical configuration

Rules:
- Implements application or domain ports.
- Maps persistence entities to domain objects.
- Avoids duplicating business rules.

## Interface Layer

Contains:
- REST controllers
- Request and response DTOs
- HTTP validation and mapping
- API-specific exception handlers

Rules:
- Controllers delegate to application use cases.
- Controllers never access JPA repositories directly.
- Domain objects are not exposed as API DTOs.

## Dependency Direction

Interfaces -> Application -> Domain
Infrastructure -> Application / Domain

Domain must not depend on outer layers.

## Bounded Contexts

Use business vocabulary and functional requirements
to identify bounded contexts.

Do not create a bounded context per:
- OpenAPI tag
- Controller
- Endpoint
- Database table

## New Projects

Apply this structure by default when the project
has no existing architectural standards.

## Existing Projects

- Inspect the established architecture first.
- Reuse compatible domain and application components.
- Avoid duplicating aggregates or use cases.
- Prefer minimal authorized modifications.
- Report architectural inconsistencies.
- Do not perform broad refactoring without approval.

## Examples of Violations

- JPA annotations in domain entities.
- Business logic implemented in controllers.
- Controllers calling Spring Data repositories.
- HTTP DTOs serving as domain entities.
- Domain services depending on infrastructure.
