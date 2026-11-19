# FastAPI Testing Guidance

Use an in-process app fixture with `TestClient` or `httpx.AsyncClient` and an
ASGI transport. Assert validation responses, response models, and the generated
`/openapi.json` document. Keep persistence behind a test double unless the
consumer explicitly supplies an isolated test database.
