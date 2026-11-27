# FastAPI Testing Guidance

Follow `references/backend-unit-testing.md` to map each `TC-*` case to its
layer. All four layers must have tests before a case is `VALIDATED`.

## Domain Layer

Use plain pytest — no FastAPI, SQLAlchemy, or Pydantic imports inside `domain`.

```python
# tests/<context>/domain/test_<aggregate>.py
def test_create_raises_domain_error_on_invalid_input():
    with pytest.raises(SomeDomainError):
        SomeAggregate.create(invalid_value)
```

Verify invariants, aggregate construction, value-object validation, and domain
service operations in isolation.

## Application Layer

Instantiate use cases with in-memory fake ports (implement the `Protocol`).

```python
# tests/<context>/application/test_<use_case>.py
class FakeRepository:
    def __init__(self): self._store = {}
    def save(self, entity): self._store[entity.id] = entity
    def find_by_id(self, id): return self._store.get(id)

def test_use_case_raises_not_found_for_missing_id():
    uc = SomeUseCase(repo=FakeRepository())
    with pytest.raises(NotFoundError):
        uc.execute(SomeCommand(id="nonexistent"))
```

No database, no HTTP, no Pydantic schemas from `interfaces`. One test per
`TC-*` case minimum.

## Infrastructure Layer

Use an isolated, in-memory or disposable SQLite/Postgres database — never the
production database. Spin it up in a pytest fixture.

```python
# tests/<context>/infrastructure/test_<repository>.py
@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s

def test_repository_returns_none_for_missing_record(session):
    repo = SqlAlchemyRepository(session)
    assert repo.find_by_id("missing") is None
```

Do not start the web application. Cover persistence invariants and
boundary conditions declared in `TC-*` cases.

## Interfaces Layer

Use an in-process app fixture with fake use cases injected through
`app.dependency_overrides`.

```python
# tests/<context>/interfaces/test_<router>.py
@pytest.fixture
def client(app):
    app.dependency_overrides[get_use_case] = lambda: FakeUseCase()
    return TestClient(app)

def test_post_returns_422_on_missing_required_field(client):
    response = client.post("/items", json={})
    assert response.status_code == 422
```

For approved OpenAPI contracts, validate real request and response exchanges
with `schemathesis` or `openapi-core`. Document supported constructs and
limitations; generated OpenAPI compatibility alone is not runtime conformance.

