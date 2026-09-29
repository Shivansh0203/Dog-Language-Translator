"""Shared pytest fixtures.

These tests run against a REAL PostgreSQL database configured via
TEST_DATABASE_URL (see .env.example) - not SQLite - so behavior (UUID
columns, timezone-aware timestamps, etc.) matches production. Point
TEST_DATABASE_URL at a disposable database; each test session drops and
recreates all tables.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db import Base, get_db
from app.core.rate_limit import limiter
import app.models  # noqa: F401 registers all models on Base.metadata
from app.main import app

settings = get_settings()

engine = create_engine(settings.test_database_url, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(scope="session", autouse=True)
def _create_test_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Wipe rows between tests so each test starts from a clean slate
        # without paying for a schema drop/create every time.
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture()
def client(db_session):
    limiter.clear()
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def register_payload():
    return {
        "email": "alex@example.com",
        "username": "alex_morgan",
        "password": "correct-horse-1",
        "pet": {
            "name": "Bruno",
            "breed": "Golden Retriever",
            "age": "2 years",
            "gender": "female",
        },
    }
