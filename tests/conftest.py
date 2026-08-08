import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registers all mappers)
from app.core.auth import verify_firebase_token
from app.core.database import Base, get_db
from app.main import app

DEFAULT_FIREBASE_UID = "test-firebase-uid"


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        Base.metadata.drop_all(eng)
        eng.dispose()


@pytest.fixture()
def db_session(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """TestClient with the DB and Firebase-token dependencies overridden.

    The mocked identity (`client.auth_uid`) defaults to DEFAULT_FIREBASE_UID
    and can be reassigned mid-test to simulate a different logged-in user
    for authorization tests.
    """

    def override_get_db():
        yield db_session

    state = {"uid": DEFAULT_FIREBASE_UID}

    def override_verify_token():
        return {"uid": state["uid"]}

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_firebase_token] = override_verify_token
    try:
        test_client = TestClient(app)
        test_client.auth_uid = state
        yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def client_no_auth_override(db_session):
    """TestClient with only the DB overridden - real token verification runs."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def shadchan_id(client):
    resp = client.post(
        "/api/v1/shadchanim",
        json={"name": "R. Test", "phone": "050-000-0000", "email": "test@example.com"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]
