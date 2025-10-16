import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import database, models

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    models.Base.metadata.drop_all(bind=database.engine)
    models.Base.metadata.create_all(bind=database.engine)
    yield
    models.Base.metadata.drop_all(bind=database.engine)


def test_register_user():
    response = client.post("/register", data={"username": "alice"})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_register_same_user_twice():
    client.post("/register", data={"username": "bob"})
    response = client.post("/register", data={"username": "bob"})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_action_increment():
    client.post("/register", data={"username": "john"})
    response = client.post("/action", data={"username": "john", "action": "inc"})
    data = response.json()
    assert response.status_code == 200
    assert data["user_count"] == 1
    assert data["total"] == 1


def test_action_decrement_and_reset():
    client.post("/register", data={"username": "kate"})
    client.post("/action", data={"username": "kate", "action": "inc"})
    client.post("/action", data={"username": "kate", "action": "inc"})
    response = client.post("/action", data={"username": "kate", "action": "dec"})
    data = response.json()
    assert data["user_count"] == 1

    response = client.post("/action", data={"username": "kate", "action": "reset"})
    data = response.json()
    assert data["user_count"] == 0


def test_total_count_across_users():
    client.post("/register", data={"username": "a"})
    client.post("/register", data={"username": "b"})
    client.post("/action", data={"username": "a", "action": "inc"})
    client.post("/action", data={"username": "b", "action": "inc"})
    client.post("/action", data={"username": "b", "action": "inc"})
    response = client.get("/stats", params={"username": "a"})
    data = response.json()
    assert data["total"] == 3


def test_stats_for_new_user():
    client.post("/register", data={"username": "tom"})
    response = client.get("/stats", params={"username": "tom"})
    data = response.json()
    assert data["user_count"] == 0
    assert isinstance(data["total"], int)
