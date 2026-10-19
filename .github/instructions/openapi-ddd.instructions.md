
---
applyTo: "**/openapi/**,**/api/**,**/*openapi*.yaml,**/*openapi*.yml,**/*openapi*.json"
---

# OpenAPI and DDD Engineering Standards

## Purpose

Implement Java APIs from OpenAPI contracts
using approved Domain-Driven Design principles.

Support both new and existing projects.

## Contract First

- Treat the approved OpenAPI document as
  the authoritative HTTP API contract.
- Validate the contract before implementation.
- Preserve declared paths, methods, request
  schemas, responses and security requirements.
- Never silently modify the approved contract.
- Detect breaking changes before implementation.

## Domain-Driven Design

- Identify domain concepts and business rules.
- Do not assume an endpoint equals an aggregate.
- Separate domain, application and infrastructure.
- Keep domain logic independent of HTTP and JPA.
- Use repository abstractions where appropriate.
- Preserve existing bounded contexts.

## Existing Projects

Before implementing:

1. Inspect existing packages and modules.
2. Identify reusable domain components.
3. Analyze existing API contracts.
4. Identify affected consumers.
5. Document potential compatibility risks.
6. Define the authorized modification scope.

Never overwrite existing functionality
without explicit approval.

## Database Integration

If implementation requires database
structural changes:

- Apply the Liquibase XML governance policy.
- Create new XML changesets.
- Preserve previously executed changesets.
- Never generate uncontrolled schema DDL.
- Do not use automatic schema updates.

## Contract Testing

- Generate tests based on the OpenAPI contract.
- Verify HTTP status codes.
- Verify request and response schemas.
- Verify required fields and constraints.
- Validate error responses.
- Verify backward compatibility for existing APIs.

## Required Output

Provide:

- Contract analysis
- Proposed DDD structure
- Impact assessment
- Implementation plan
- Database structural change requirements
- Required contract tests
- Compatibility risks
