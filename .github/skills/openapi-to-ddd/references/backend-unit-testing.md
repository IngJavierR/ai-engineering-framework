# Backend Unit Testing by Layer

Each `TC-*` case declared in `test-cases.yaml` describes a scenario that
exercises the full backend stack. Derive focused tests for every layer that
independently enforces part of that scenario. The interface layer alone is
not sufficient evidence.

## Mapping TC-* Cases to Layers

For every `TC-*` case decide which layers own the asserted behavior:

| Layer | What to test | Precondition |
| --- | --- | --- |
| `domain` | The invariant or business rule the case validates | No app, database, or HTTP import allowed |
| `application` | The use-case orchestration given the case's input | Fake port implementations only |
| `infrastructure` | The adapter behavior against a real or in-memory store | Isolated, disposable store; no web app |
| `interfaces` | HTTP status, schema, validation errors, error contract | In-process app with fake application dependencies |

A single `TC-*` case may produce tests at multiple layers when each layer
independently enforces part of the scenario. Mark a layer `N/A` only when the
case describes behavior that does not exist at that layer (for example, a pure
HTTP schema-validation case with no corresponding domain rule). Never mark a
layer `NOT_RUN` without explaining why.

## Domain Layer Tests

**Scope:** entities, value objects, aggregates, domain services, domain errors.

- Test one invariant or rule per test.
- Positive `TC-*` cases: construct valid aggregates or run domain service
  operations and assert the resulting state or domain events.
- Negative `TC-*` cases that map to a domain invariant: attempt the invalid
  construction or state transition and assert that the declared domain
  exception is raised.
- Boundary `TC-*` cases: exercise the declared boundary value and assert the
  expected accept or reject behavior.
- **No web framework, ORM, database, or DI container may be imported.**
  Fail the test if any such import appears in the domain under test.

## Application Layer Tests

**Scope:** use cases, commands, queries, application services.

- Instantiate each use case with fake ports (in-memory stubs or test doubles).
- Positive `TC-*` cases: call the use case with the case's declared input data
  and assert the returned result matches the response-schema fields.
- Negative `TC-*` cases: supply invalid or missing input as declared; assert
  that the appropriate domain or application error is raised and that no
  side-effect reached the fake store.
- Group tests by use case. One test per `TC-*` case minimum.
- **Do not access the database, HTTP client, or ORM. Use fake ports only.**

## Infrastructure Layer Tests

**Scope:** persistence adapters, external service adapters, mappers.

- Use an isolated, disposable store (in-memory or test-container).
- For each `TC-*` case that depends on stored state:
  - Seed the store to satisfy the case's precondition.
  - Call the repository or adapter method.
  - Assert the resulting stored or returned state matches the case expectation.
- Cover boundary conditions declared in cases: missing records (expect not-found
  error), duplicate key violations, declared constraint errors.
- **Do not start the web application.**

## Interfaces Layer Tests

**Scope:** routers, controllers, exception handlers, request/response DTOs.

- Use the in-process app fixture with fake application-layer dependencies
  (do not use real use cases backed by real stores).
- For each `TC-*` case: issue the declared HTTP request and assert the declared
  `status` code and `responseSchema` fields.
- Include every negative case: required property missing, wrong type, declared
  format violation, unauthorized call.
- Validate the generated OpenAPI document against the approved contract.

## Evidence per TC-* Case

Report the layer result for every declared case identifier:

```
TC-001  domain=PASS  application=PASS  infrastructure=PASS  interfaces=PASS
TC-002  domain=PASS  application=PASS  infrastructure=NOT_RUN(no persistence)  interfaces=PASS
TC-003  domain=N/A   application=PASS  infrastructure=NOT_RUN(no persistence)  interfaces=PASS
```

A `NOT_RUN` at any layer blocks `VALIDATED` for that case. `N/A` requires a
brief justification. Do not report `PASS` for a check that was not executed.
