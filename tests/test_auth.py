import datetime

import pytest
from sqlalchemy import select

from app import auth
from app.db import SessionLocal, utcnow
from app.models import LoginSession, User
from tests.conftest import PASSWORD, csrf_from


def login(c, password):
    token = csrf_from(c.get("/login").text)
    return c.post("/login", data={"password": password, "csrf_token": token},
                  follow_redirects=False)


def test_login_sets_strict_secure_cookie(anon):
    r = login(anon, PASSWORD)
    assert r.status_code == 303 and r.headers["location"] == "/"
    cookie = [h for h in r.headers.get_list("set-cookie") if h.startswith("laner_session=")][0]
    lowered = cookie.lower()
    assert "httponly" in lowered and "secure" in lowered and "samesite=strict" in lowered
    assert anon.get("/", follow_redirects=False).status_code == 200


def test_wrong_password(anon):
    r = login(anon, "nope nope nope")
    assert r.status_code == 401 and "Wrong password" in r.text
    assert anon.get("/", follow_redirects=False).status_code == 303


def test_login_needs_csrf(anon):
    r = anon.post("/login", data={"password": PASSWORD, "csrf_token": "x"})
    assert r.status_code == 403


def test_lockout_after_five_failures(anon):
    for _ in range(auth.LoginLimiter.MAX_FAILURES):
        assert login(anon, "wrong wrong wrong").status_code == 401
    # Locked: even the right password is refused now.
    r = login(anon, PASSWORD)
    assert r.status_code == 429 and "Too many" in r.text


def test_limiter_unlocks_after_lockout():
    now = [0.0]
    limiter = auth.LoginLimiter(clock=lambda: now[0])
    for _ in range(limiter.MAX_FAILURES):
        limiter.record_failure()
    assert limiter.seconds_locked() == limiter.LOCKOUT
    now[0] += limiter.LOCKOUT
    assert limiter.seconds_locked() == 0


def test_old_failures_expire():
    now = [0.0]
    limiter = auth.LoginLimiter(clock=lambda: now[0])
    for _ in range(limiter.MAX_FAILURES - 1):
        limiter.record_failure()
    now[0] += limiter.WINDOW + 1
    limiter.record_failure()
    assert limiter.seconds_locked() == 0


def test_logout_kills_session(client):
    token = client.cookies.get(auth.SESSION_COOKIE)
    page = client.get("/")
    r = client.post("/logout", data={"csrf_token": csrf_from(page.text)}, follow_redirects=False)
    assert r.headers["location"] == "/login"
    client.cookies.set(auth.SESSION_COOKIE, token)   # replaying the old cookie...
    assert client.get("/", follow_redirects=False).status_code == 303   # ...doesn't work


def test_expired_session_rejected(client):
    with SessionLocal() as s:
        for row in s.scalars(select(LoginSession)):
            row.expires_at = utcnow() - datetime.timedelta(seconds=1)
        s.commit()
    assert client.get("/", follow_redirects=False).status_code == 303


def test_changing_password_logs_everyone_out(client):
    with SessionLocal() as s:
        auth.set_password(s, "a brand new password")
    assert client.get("/", follow_redirects=False).status_code == 303


def test_stored_secrets_are_hashed(client):
    token = client.cookies.get(auth.SESSION_COOKIE)
    with SessionLocal() as s:
        assert s.get(User, 1).password_hash.startswith("$argon2id$")
        hashes = list(s.scalars(select(LoginSession.token_hash)))
    assert token not in hashes and len(hashes) == 1


def test_password_rules():
    with SessionLocal() as s:
        for bad in ["short", "x" * (auth.PASSWORD_MAX + 1)]:
            with pytest.raises(ValueError):
                auth.set_password(s, bad)


def test_setup_message_when_no_password(anon):
    with SessionLocal() as s:
        s.delete(s.get(User, 1))
        s.commit()
    assert "No password has been set yet" in anon.get("/login").text
