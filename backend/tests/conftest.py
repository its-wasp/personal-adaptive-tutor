"""
Shared pytest fixtures and test-time configuration.

Set dummy environment variables BEFORE importing anything from ``app`` so
``app.config.Settings`` resolves to deterministic values regardless of the
host machine / CI (there is no ``.env`` in CI). Settings already have safe
defaults, so this is mostly belt-and-suspenders + a fixed JWT secret.

No live database is required: the SQLAlchemy engine is created lazily and
none of the tests here execute a query against it.
"""
import os

os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    """A FastAPI TestClient for endpoint-level tests that don't touch the DB."""
    with TestClient(app) as c:
        yield c
