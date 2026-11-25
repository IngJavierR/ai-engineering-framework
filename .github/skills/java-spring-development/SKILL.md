---
name: java-spring-development
description: >
  Java and Spring Boot engineering standards for backend services: DDD
  package layout, error handling, database integrity mapping, security,
  JUnit 5 and Mockito testing, and validation evidence. Use for any work on
  Java source files, Maven or Gradle builds, Spring configuration, or JPA
  persistence adapters.
---

# Java Spring Development

## Mission

Apply consistent Java and Spring Boot engineering practices to backend work.
The architecture follows `backend-ddd-architecture`; this skill maps it to
Java. Read [the Java DDD layout](./references/ddd-layout.md) before creating,
moving, or reviewing packages.

## General Principles

- Prefer simple, maintainable implementations.
- Follow SOLID principles where appropriate.
- Avoid unnecessary abstractions.
- Prefer composition over inheritance.
- Do not duplicate business logic.
- Preserve existing public contracts.
- Use meaningful English identifiers.
- Do not introduce dependencies without justification.

## Architecture

- Identify the existing architecture before coding.
- Preserve module and package boundaries.
- New projects and new bounded contexts use the Java DDD layout.
- Keep business logic separate from infrastructure.
- Do not access persistence directly from controllers.
- Do not couple domain objects to HTTP models.
- Use constructor-based dependency injection for external dependencies.
- Keep Spring, JPA, and other framework concerns outside the domain.

## Error Handling

- Use explicit error handling.
- Do not silently swallow exceptions.
- Do not expose sensitive implementation details.
- Use meaningful domain exceptions when appropriate.
- Follow existing error contracts.
- Translate database integrity failures to domain exceptions only when the
  specific violated constraint is identified.
- For PostgreSQL, use the SQLSTATE and constraint name when available; do not
  map every `DataIntegrityViolationException` to the same HTTP error.

## Security

- Never hardcode credentials or secrets.
- Validate input at trust boundaries.
- Use parameterized database queries.
- Avoid logging credentials and sensitive data.
- Respect authorization requirements.
- Avoid introducing vulnerable dependencies.

## Testing

- Generate meaningful unit tests for new behavior.
- Cover positive, negative, and boundary scenarios.
- Use JUnit 5 for projects where it is approved.
- Use Mockito when mocking is appropriate.
- Avoid mocking pure domain logic unnecessarily.
- Preserve existing regression tests.
- Never disable failing tests to make a build pass.
- Isolate transactions in tests that intentionally cause SQL failures. A
  failed PostgreSQL statement can leave its transaction aborted until
  rollback.
- Do not apply `@Transactional` indiscriminately to JDBC constraint tests; use
  a transaction boundary appropriate to the assertion.
- When Docker or Testcontainers is used for validation, verify that the
  selected runtime versions are compatible. Do not make either tool a
  framework dependency solely for this purpose.

## Database

- Use Liquibase XML for all database structural changes; follow
  `liquibase-versioning`.
- Never modify previously executed changesets.
- Never use Hibernate or JPA automatic DDL (`spring.jpa.hibernate.ddl-auto`
  other than `none` or `validate`) to create or modify managed schemas.
- Keep domain objects independent of JPA entities.

## Validation Evidence

| Check | Default command |
| --- | --- |
| Compile | `mvn -q -DskipTests compile` |
| Unit and integration tests | `mvn test` |
| Architecture rules | ArchUnit test or import scan described in the layout reference |
| Liquibase | Maven `validate` and `update` against a disposable database |
| Generated OpenAPI | springdoc `/v3/api-docs` |

Prefer the consumer's declared commands when they differ.

- Use `GENERATED` only for produced artifacts; it does not imply compilation.
- Use `COMPILED` only with evidence of successful compilation.
- Use `TESTED` only with verifiable test results and known scope.
- Use `VALIDATED` only when the declared acceptance criteria have sufficient
  evidence; generated artifacts or static inspection alone are insufficient.
- Report `NOT_RUN` for pending applicable verifications.

## Change Management

Before editing existing code:

1. Inspect the relevant implementation.
2. Identify dependencies and affected contracts.
3. Define the intended modification scope.
4. Preserve unrelated functionality.
5. Implement the smallest correct change.
6. Run applicable tests.
7. Report executed and unexecuted validations.

## Completion Requirements

Report:

- Files modified and their DDD layer.
- Reason for each modification.
- Tests executed and results.
- Potential compatibility impacts.
- Remaining risks or limitations.

Never claim that quality checks passed unless their execution is supported by
evidence.
