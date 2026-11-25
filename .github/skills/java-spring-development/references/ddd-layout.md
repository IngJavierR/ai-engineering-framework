# Java Spring DDD Layout

Java mapping of `backend-ddd-architecture`. Existing projects preserve their
approved architecture unless a change is authorized.

## Unit of Modularity

One root package per bounded context: `com.<company>.<context>`. A multi-module
build may use one Maven or Gradle module per context; the inner layout stays
the same.

## Package Layout

```text
com.company.context/
  domain/
    model/          entities, value objects, aggregates
    event/          domain events
    service/        domain services
    port/           repository and domain-owned ports
  application/
    usecase/        use cases / application services
    command/
    query/
    port/           ports for external capabilities
  infrastructure/
    persistence/    JPA entities, Spring Data repositories, adapters, mappers
    integration/    external clients and messaging adapters
    configuration/  Spring configuration and bean wiring
  interfaces/
    rest/
      dto/          request and response DTOs
      mapper/       DTO <-> application mapping
                    controllers and exception handlers
```

## Framework-Free Domain

Forbidden in `domain`:

- Spring annotations and types (`@Component`, `@Service`, `@Transactional`,
  `org.springframework.*`).
- JPA and Hibernate annotations and types (`jakarta.persistence.*`,
  `javax.persistence.*`, `org.hibernate.*`).
- HTTP, servlet, Jackson, or validation-framework types bound to transport.

`@Transactional` belongs to `application` use cases or infrastructure
adapters.

## Persistence Separation

- JPA entities live in `infrastructure/persistence` and are never exposed
  outside it.
- Persistence adapters implement `domain/port` or `application/port`
  interfaces and map JPA entities to domain objects.

## Inbound Adapters

- Controllers live in `interfaces/rest` and delegate to application use cases.
- Controllers never call Spring Data repositories.
- Domain objects are never returned as API DTOs.
- `@RestControllerAdvice` maps domain and application exceptions to the
  approved error contract.

## Composition Root

Bean wiring lives in `infrastructure/configuration` and the Spring Boot
application class. Domain types are plain Java objects instantiated through
factories or use cases.

## Dependency Enforcement

Prefer an ArchUnit test, for example:

```java
noClasses().that().resideInAPackage("..domain..")
    .should().dependOnClassesThat()
    .resideInAnyPackage("org.springframework..", "jakarta.persistence..",
        "javax.persistence..", "org.hibernate..", "..infrastructure..",
        "..interfaces..");
```

Without ArchUnit, report an import scan of `domain` as static evidence only.

## Tests

| Layer | Location | Tooling |
| --- | --- | --- |
| Domain | `src/test/java/.../domain` | JUnit 5, no Spring context |
| Application | `src/test/java/.../application` | JUnit 5, Mockito for ports |
| Persistence adapters | `src/test/java/.../infrastructure` | Spring Data slice or Testcontainers |
| REST and contract | `src/test/java/.../interfaces` | MockMvc/WebTestClient with OpenAPI validation |

## Migrations

Liquibase XML changelogs live under `src/main/resources/db/changelog`. Set
`spring.jpa.hibernate.ddl-auto` to `none` or `validate`.

## Violations

- JPA annotations in domain entities.
- Business logic implemented in controllers.
- Controllers calling Spring Data repositories.
- HTTP DTOs serving as domain entities.
- Domain services depending on infrastructure.
