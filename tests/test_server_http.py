import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture
def client():
    server.manager.functions.clear()
    with TestClient(server.app) as c:
        yield c
    server.manager.functions.clear()


def _payload(name="sq", expr="x**2 + y**2"):
    return {"name": name, "inputs": ["x", "y"], "outputs": ["z"], "expression": expr}


def test_create_function(client):
    resp = client.post("/functions", json=_payload())
    assert resp.status_code == 200
    assert resp.json()["name"] == "sq"


def test_create_duplicate_returns_400(client):
    client.post("/functions", json=_payload())
    resp = client.post("/functions", json=_payload())
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_list_functions(client):
    client.post("/functions", json=_payload(name="a"))
    client.post("/functions", json=_payload(name="b"))
    resp = client.get("/functions")
    assert resp.status_code == 200
    assert {f["name"] for f in resp.json()} == {"a", "b"}


def test_get_function(client):
    client.post("/functions", json=_payload())
    resp = client.get("/functions/sq")
    assert resp.status_code == 200
    assert resp.json()["expression"] == "x**2 + y**2"


def test_get_function_not_found(client):
    resp = client.get("/functions/missing")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Function not found"


def test_update_function(client):
    client.post("/functions", json=_payload())
    resp = client.put("/functions/sq", json=_payload(expr="x + y"))
    assert resp.status_code == 200
    assert resp.json()["expression"] == "x + y"


def test_update_function_not_found(client):
    resp = client.put("/functions/missing", json=_payload(name="missing"))
    assert resp.status_code == 404


def test_delete_function(client):
    client.post("/functions", json=_payload())
    resp = client.delete("/functions/sq")
    assert resp.status_code == 200
    assert resp.json() == {"status": "deleted"}
    assert client.get("/functions/sq").status_code == 404


def test_delete_function_not_found(client):
    resp = client.delete("/functions/missing")
    assert resp.status_code == 404


def test_execute_function(client):
    client.post("/functions", json=_payload())
    resp = client.post("/functions/sq/execute", json={"args": {"x": 3, "y": 4}})
    assert resp.status_code == 200
    assert resp.json() == {"result": 25}


def test_execute_function_missing_args_returns_400(client):
    client.post("/functions", json=_payload())
    resp = client.post("/functions/sq/execute", json={"args": {"x": 3}})
    assert resp.status_code == 400
    assert "Missing arguments" in resp.json()["detail"]


def test_execute_missing_function_returns_400(client):
    resp = client.post("/functions/ghost/execute", json={"args": {"x": 1}})
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"]
