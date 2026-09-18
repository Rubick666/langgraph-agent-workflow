import os

# Set a separate test DB BEFORE importing the app
os.environ["DATABASE_PATH"] = "./data/test_workflow.db"

from fastapi.testclient import TestClient

from app.main import app


def pytest_sessionfinish(session, exitstatus):
    """Clean up the test DB file after the session."""
    for suffix in ("", "-shm", "-wal"):
        p = f"./data/test_workflow.db{suffix}"
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


import pytest


@pytest.fixture(scope="session")
def client():
    """Single TestClient for the whole test session.

    Its `with` block runs the FastAPI lifespan, which compiles the graph and
    warms up the LLM. The same event loop is reused across all requests.
    """
    with TestClient(app) as c:
        yield c