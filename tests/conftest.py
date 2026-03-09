import sys
import os
import pytest
from fastapi.testclient import TestClient

# add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import init_db, get_connection


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Initialize DB pool once for the test session.
    """
    init_db()


@pytest.fixture(autouse=True)
def clean_database():
    """
    Clear the contact table before each test.
    """
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("DELETE FROM contact")

    conn.commit()


@pytest.fixture
def client():
    return TestClient(app)