"""
Shared pytest configuration and database fixtures.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.main import app
from app.models import user, profile, resume, roadmap, assessment, mentorship  # noqa: F401

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield
    db.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session(setup_db):
    """A direct DB session bound to the same in-memory test database."""
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def make_user(client):
    """
    Factory fixture: registers + logs in a user and returns auth headers.

        headers, payload = make_user(email=..., role="student")
    """
    def _make(
        email: str = "student@example.com",
        role: str = "student",
        password: str = "Password123!",
        full_name: str = "Test Student",
    ):
        client.post(
            "/auth/register",
            json={"email": email, "full_name": full_name, "password": password, "role": role},
        )
        res = client.post("/auth/login", json={"email": email, "password": password})
        assert res.status_code == 200, res.text
        payload = res.json()
        headers = {"Authorization": f"Bearer {payload['access_token']}"}
        return headers, payload

    return _make
