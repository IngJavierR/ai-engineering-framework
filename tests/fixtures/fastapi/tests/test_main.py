from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_echo_contract_and_validation() -> None:
    assert client.post("/echo", json={"message": "hello"}).json() == {"message": "hello"}
    assert client.post("/echo", json={"message": ""}).status_code == 422
    assert client.post("/echo", json={"message": "forbidden"}).status_code == 403
    assert client.get("/openapi.json").status_code == 200
