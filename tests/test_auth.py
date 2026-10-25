from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.models import Role
from tests.conftest import PASSWORD


def test_register_creates_user_role(client):
    r = client.post("/auth/register", json={"username": "newbie", "password": PASSWORD})
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "newbie"
    assert body["role"] == "user"
    assert "hashed_password" not in body


def test_register_cannot_choose_admin_role(client):
    r = client.post(
        "/auth/register",
        json={"username": "sneaky", "password": PASSWORD, "role": "admin"},
    )
    assert r.status_code == 201
    assert r.json()["role"] == "user" 

def test_register_duplicate_username_409(client):
    payload = {"username": "dupe", "password": PASSWORD}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_register_short_password_422(client):
    r = client.post("/auth/register", json={"username": "shorty", "password": "abc"})
    assert r.status_code == 422


def test_login_success_returns_token(client, make_user):
    make_user("alice", Role.USER)
    r = client.post("/auth/login", data={"username": "alice", "password": PASSWORD})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password_401(client, make_user):
    make_user("alice", Role.USER)
    r = client.post("/auth/login", data={"username": "alice", "password": "wrong-pass"})
    assert r.status_code == 401


def test_login_unknown_user_401(client):
    r = client.post("/auth/login", data={"username": "ghost", "password": PASSWORD})
    assert r.status_code == 401


def test_me_with_valid_token(client, alice):
    r = client.get("/auth/me", headers=alice)
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_me_without_token_401(client):
    assert client.get("/auth/me").status_code == 401


def test_garbage_token_401(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert r.status_code == 401


def test_expired_token_401(client, make_user):
    user_id = make_user("alice", Role.USER)
    expired = jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_token_for_deleted_user_401(client, auth_headers):
    r = client.get("/auth/me", headers=auth_headers(9999))
    assert r.status_code == 401