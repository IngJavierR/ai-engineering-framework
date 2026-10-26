
---
applyTo: "**/*.java"
---

# Java Engineering Standards

## Purpose

Apply consistent Java engineering practices
to all Java source files.

These instructions complement the repository-wide
engineering rules.

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
- Keep business logic separate from infrastructure.
- Do not access persistence directly from controllers.
- Do not couple domain objects to HTTP models.
- Use dependency injection for external dependencies.
- Do not introduce architectural patterns that conflict
  with the existing project's approved architecture.

## Domain-Driven Design

When DDD is required by project policies:

- Keep domain logic in the domain layer.
- Identify entities and value objects.
- Respect aggregate boundaries.
- Use repositories as persistence abstractions.
- Place use-case orchestration in the application layer.
- Keep framework-specific concerns outside the domain.
- Do not infer bounded contexts solely from API paths.

## Error Handling

- Use explicit error handling.
- Do not silently swallow exceptions.
- Do not expose sensitive implementation details.
- Use meaningful domain exceptions when appropriate.
- Follow existing error contracts.
- Translate database integrity failures to domain exceptions only
  when the specific violated constraint is identified.
- For PostgreSQL, use the SQLSTATE and constraint name when
  available; do not map every DataIntegrityViolationException
  to the same HTTP error.

## Security

- Never hardcode credentials or secrets.
- Validate input at trust boundaries.
- Use parameterized database queries.
- Avoid logging credentials and sensitive data.
- Respect authorization requirements.
- Avoid introducing vulnerable dependencies.

## Testing

- Generate meaningful unit tests for new behavior.
- Cover positive, negative and boundary scenarios.
- Use JUnit 5 for projects where it is approved.
- Use Mockito when mocking is appropriate.
- Avoid mocking pure domain logic unnecessarily.
- Preserve existing regression tests.
- Never disable failing tests to make a build pass.
- Isolate transactions in tests that intentionally cause SQL
  failures. A failed PostgreSQL statement can leave its transaction
  aborted until rollback.
- Do not apply @Transactional indiscriminately to JDBC constraint
  tests; use a transaction boundary appropriate to the assertion.
- When Docker or Testcontainers is used for validation, verify the
  selected runtime versions are compatible. Do not make either tool
  a framework dependency solely for this purpose.

## Validation Evidence

- Use GENERATED only for produced artifacts; it does not imply
  compilation.
- Use COMPILED only with evidence of successful compilation.
- Use TESTED only with verifiable test results and known scope.
- Use VALIDATED only when the declared acceptance criteria have
  sufficient evidence; generated artifacts or static inspection alone
  are insufficient.
- Report NOT_RUN for pending applicable verifications.

## Database

- Use Liquibase for all database schema changes.
- Never modify previously executed changesets.
- Do not use automatic schema updates in environments
  with managed database migrations.
- Keep domain objects independent of persistence entities
  when required by the architecture.

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
- Files modified.
- Reason for each modification.
- Tests executed and results.
- Potential compatibility impacts.
- Remaining risks or limitations.

Never claim that quality checks passed unless
their execution is supported by evidence.
