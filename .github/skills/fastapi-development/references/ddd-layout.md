# Python FastAPI DDD Layout

Python mapping of `backend-ddd-architecture`. Existing projects preserve their
approved architecture unless a change is authorized.

## Unit of Modularity

One Python package per bounded context under the application package:
`app/<context>/`. Use snake_case package names.

## Package Layout

```text
app/
  main.py                 FastAPI app factory and composition root
  <context>/
    domain/
      model.py            entities, value objects, aggregates (dataclasses)
      events.py
      services.py
      ports.py            repository and domain-owned ports (typing.Protocol)
      errors.py           domain exceptions
    application/
      use_cases.py        commands, queries, use cases
      ports.py            ports for external capabilities
    infrastructure/
      persistence/        ORM models, repositories implementing ports, mappers
      integration/        external clients and messaging adapters
      dependencies.py     FastAPI Depends providers and wiring
    interfaces/
      api/
        router.py         APIRouter endpoints
        schemas.py        Pydantic request and response models
        errors.py         exception handlers -> approved error contract
```

Split modules into packages when they grow; keep the layer boundaries.

## Framework-Free Domain

Forbidden in `domain`:

- `fastapi`, `starlette`, and HTTP client imports.
- ORM and database imports (`sqlalchemy`, `sqlmodel`, database drivers).
- Pydantic models used as domain entities. Use `dataclasses` or plain classes;
  Pydantic belongs to `interfaces/api/schemas.py` and configuration.

## Persistence Separation

- ORM models live in `infrastructure/persistence` and are never returned by
  routers.
- Repositories implement the `Protocol` ports and map ORM models to domain
  objects.

## Inbound Adapters

- Routers call application use cases only; they never open database sessions
  or query ORM models.
- Pydantic schemas map to commands and queries explicitly.
- Exception handlers translate domain errors without exposing stack traces.

## Composition Root

`app/main.py` and `infrastructure/dependencies.py` wire adapters to ports
through FastAPI `Depends`. Domain code never calls `Depends`.

## Dependency Enforcement

Prefer `import-linter` contracts, for example:

```ini
[importlinter:contract:domain-is-pure]
name = Domain is framework-free
type = forbidden
source_modules = app.*.domain
forbidden_modules = fastapi, starlette, sqlalchemy, sqlmodel, pydantic
```

Command: `lint-imports`. Without it, report an import scan of `domain` as
static evidence only.

## Tests

| Layer | Location | Tooling |
| --- | --- | --- |
| Domain | `tests/<context>/domain` | pytest, no app or database |
| Application | `tests/<context>/application` | pytest with fake ports |
| Persistence adapters | `tests/<context>/infrastructure` | pytest against a disposable database |
| API and contract | `tests/<context>/interfaces` | HTTPX `AsyncClient` or `TestClient` with OpenAPI validation |

## Migrations

Follow `liquibase-versioning`. Never call `metadata.create_all()` or apply
Alembic `autogenerate` output to managed schemas.

## Violations

- `sqlalchemy` or `fastapi` imports in `domain`.
- Business rules in routers or dependency providers.
- Routers using `Session` or ORM queries directly.
- Pydantic schemas or ORM models used as domain entities.
