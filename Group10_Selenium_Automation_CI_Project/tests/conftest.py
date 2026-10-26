import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Use an isolated SQLite DB; never touch the regular demonstration database.
file_path = os.path.join(tempfile.mkdtemp(prefix='campustrack-api-tests-'), 'test.db')
os.environ['APP_DB_PATH'] = file_path
os.environ['TEST_MODE'] = '1'
os.environ['TEST_TOKEN'] = 'test-python-fixture-token'

from app.main import app  # noqa: E402
from app.db import reset_for_tests  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        reset_for_tests()
        yield c


def login(c, username='admin', password='Admin@123'):
    return c.post('/admin/login' if username == 'admin' else '/student/login', data={'username': username, 'password': password}, follow_redirects=False)
