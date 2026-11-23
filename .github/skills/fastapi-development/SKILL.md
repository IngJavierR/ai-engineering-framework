---
name: fastapi-development
description: Implement and validate Python FastAPI services with typed contracts, secure configuration, tests, and scope governance.
---

# FastAPI Development

## Mission

Build or extend FastAPI services using modern typed Python, Pydantic contracts,
explicit dependency boundaries, and evidence-based validation. This capability
does not impose Spring, JPA, Java DDD, or Java-specific migration patterns.

## Service design

- Use type annotations and Pydantic request/response models at HTTP boundaries.
- Keep routers, application services, and data-access adapters separate using
  interfaces/protocols appropriate to Python.
- Treat the approved OpenAPI contract as the source of truth. `app.openapi()`
  must be compatible with it and real responses must be validated against it.
- Validate input through Pydantic and map expected domain errors to deliberate
  HTTP responses without exposing internal stack traces.
- Load secrets and environment-specific configuration from environment or a
  configured secret provider; never hardcode real credentials.

## Security and data

- Apply endpoint authentication and authorization when the consumer requires
  them; do not invent an identity provider.
- Use parameterized ORM/query APIs and protect object access at the application
  boundary.
- For database structural changes, follow `liquibase-versioning`.

## Testing and scope

- Use pytest with HTTPX `AsyncClient` or FastAPI `TestClient` according to the
  consumer's installed stack.
- Cover successful requests, validation failures, expected errors, and OpenAPI
  presence. Do not make real external calls in tests.
- Run existing format, type, test, and application commands. Record only
  executed evidence and preserve client-policy scope restrictions.
