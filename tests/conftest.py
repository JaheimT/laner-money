"""Point the app at a throwaway database before any test imports it,
and give tests a logged-in and a logged-out browser."""
import os
import re
import tempfile

os.environ["LANER_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import auth  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402

PASSWORD = "correct horse battery"


def csrf_from(page_text: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', page_text).group(1)


@pytest.fixture(autouse=True)
def fresh_limiter(monkeypatch):
    monkeypatch.setattr(auth, "limiter", auth.LoginLimiter())


@pytest.fixture
def anon():
    # https: the cookies are Secure, so a client on plain http wouldn't send them.
    with SessionLocal() as s:
        auth.set_password(s, PASSWORD)
    return TestClient(app, base_url="https://testserver")


@pytest.fixture
def client(anon):
    token = csrf_from(anon.get("/login").text)
    r = anon.post("/login", data={"password": PASSWORD, "csrf_token": token},
                  follow_redirects=False)
    assert r.status_code == 303
    return anon
