# Stack Layout Contract

## Purpose

Define what every backend stack skill must provide so that the neutral
`backend-ddd-architecture` rules apply the same way in Java, Python, .NET, and
future stacks.

## Registered Stack Mappings

| Stack | Stack skill | Layout reference |
| --- | --- | --- |
| Java Spring Boot | `java-spring-development` | `references/ddd-layout.md` |
| Python FastAPI | `fastapi-development` | `references/ddd-layout.md` |

A stack that is not listed has no approved mapping yet. Apply the neutral
layers with the stack's idiomatic naming, or report `BLOCKED` with the
concrete mapping question. Do not borrow another stack's layout.

## Required Content of a Stack Layout Reference

A stack skill is complete only when its `references/ddd-layout.md` defines:

1. **Unit of modularity**: package, module, namespace, or project per bounded
   context, and its naming convention.
2. **Layer mapping**: the concrete location of `domain`, `application`,
   `infrastructure`, and `interfaces` inside a bounded context.
3. **Dependency enforcement**: how the dependency rule is enforced (project
   references, module boundaries, architecture tests, or import linting) and
   the command that verifies it.
4. **Framework-free domain**: the framework types, annotations, decorators, or
   base classes forbidden in `domain`.
5. **Persistence separation**: where persistence models live and how they map
   to domain objects.
6. **Inbound adapters**: where controllers, routers, DTOs, and error mapping
   live.
7. **Composition root**: where dependency injection wiring happens.
8. **Tests**: the location and tooling for domain, application, adapter, and
   contract tests.
9. **Migrations**: how the stack integrates Liquibase XML without ORM
   automatic DDL.
10. **Violations**: stack-specific examples of breaking the rules.

## Adding a New Stack

1. Create `.github/skills/<stack>-development/SKILL.md` with the stack
   engineering standards.
2. Create `.github/skills/<stack>-development/references/ddd-layout.md`
   covering every item above.
3. Register the capability in `framework.yaml` with a dependency on
   `backend-ddd-architecture`, and a stack profile when needed.
4. Add the row to the registered mappings table in this file.
5. Add install and profile tests for the new capability.

Do not add language-specific `.github/instructions/*.instructions.md` files.
Stack standards are distributed as skills.
