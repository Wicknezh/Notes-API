import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-only-for-pytest-0123456789abcdef")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Role, User
from app.security import create_access_token, hash_password

PASSWORD = "password123"


@pytest.fixture()
def session_factory():
    """A fresh in-memory database for every test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False)
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # No `with` block, so the startup lifespan (which uses the real DB) does not run
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(session_factory):
    """Factory: create a user directly in the test DB and return its id."""

    def _make(username: str, role: Role) -> int:
        with session_factory() as db:
            user = User(
                username=username,
                hashed_password=hash_password(PASSWORD),
                role=role,
            )
            db.add(user)
            db.commit()
            return user.id

    return _make


@pytest.fixture()
def auth_headers():
    """Factory: build an Authorization header for a user id."""

    def _headers(user_id: int) -> dict:
        return {"Authorization": f"Bearer {create_access_token(user_id)}"}

    return _headers


@pytest.fixture()
def admin(make_user, auth_headers):
    return auth_headers(make_user("admin", Role.ADMIN))


@pytest.fixture()
def alice(make_user, auth_headers):
    return auth_headers(make_user("alice", Role.USER))


@pytest.fixture()
def bob(make_user, auth_headers):
    return auth_headers(make_user("bob", Role.USER))


@pytest.fixture()
def viewer(make_user, auth_headers):
    return auth_headers(make_user("victor", Role.VIEWER))