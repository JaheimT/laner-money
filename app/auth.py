"""Login: password hashing, sessions and login rate limiting.

- Passwords: Argon2id via argon2-cffi (no hand-rolled crypto). The password
  is set with `python -m app.cli set-password`, never stored in code.
- Sessions: a random 256-bit token in an HttpOnly, Secure, SameSite=Strict
  cookie. The database stores only the token's SHA-256, so someone who gets
  a copy of the database or a backup can't turn it into a login.
- Rate limiting: after MAX_FAILURES wrong passwords within WINDOW, login is
  locked for LOCKOUT, whoever is trying.
"""

import datetime
import hashlib
import secrets
import threading
import time
from collections import deque

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.models import LoginSession, User

PASSWORD_MIN = 12
PASSWORD_MAX = 256           # Argon2 is happy with long input; this just caps work
SESSION_COOKIE = "laner_session"
SESSION_LIFETIME = datetime.timedelta(days=14)

# argon2-cffi's defaults are Argon2id with the RFC 9106 "low memory" profile
# (64 MiB, 3 passes): slow for an attacker guessing, ~50 ms for one login.
_hasher = PasswordHasher()
# Used when no password is set yet, so "no user" takes as long as "wrong password".
_DUMMY_HASH = _hasher.hash("not-a-real-password")


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
def check_new_password(password: str) -> str | None:
    """Return a problem with a proposed password, or None if it's fine."""
    if len(password) < PASSWORD_MIN:
        return f"Password must be at least {PASSWORD_MIN} characters."
    if len(password) > PASSWORD_MAX:
        return f"Password must be {PASSWORD_MAX} characters or fewer."
    return None


def password_is_set(session: Session) -> bool:
    return session.get(User, 1) is not None


def set_password(session: Session, password: str) -> None:
    """Set (or change) the password. Logs out every existing session."""
    problem = check_new_password(password)
    if problem:
        raise ValueError(problem)
    user = session.get(User, 1) or User(id=1)
    user.password_hash = _hasher.hash(password)
    user.updated_at = utcnow()
    session.add(user)
    session.execute(delete(LoginSession))
    session.commit()


def verify_password(session: Session, password: str) -> bool:
    if len(password) > PASSWORD_MAX:
        return False
    user = session.get(User, 1)
    try:
        _hasher.verify(user.password_hash if user else _DUMMY_HASH, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    if user is None:
        return False
    # If argon2-cffi's recommended settings get stronger in an update,
    # upgrade the stored hash the next time the right password is typed.
    if _hasher.check_needs_rehash(user.password_hash):
        user.password_hash = _hasher.hash(password)
        session.commit()
    return True


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(session: Session) -> str:
    """Start a login session; returns the token to put in the cookie."""
    now = utcnow()
    # Tidy up: expired sessions are useless, so don't keep them around.
    session.execute(delete(LoginSession).where(LoginSession.expires_at <= now))
    token = secrets.token_urlsafe(32)
    session.add(LoginSession(token_hash=_hash_token(token), created_at=now,
                             expires_at=now + SESSION_LIFETIME))
    session.commit()
    return token


def session_is_valid(session: Session, token: str | None) -> bool:
    if not token or len(token) > 100:
        return False
    row = session.scalar(select(LoginSession).where(
        LoginSession.token_hash == _hash_token(token)))
    return row is not None and row.expires_at > utcnow()


def end_session(session: Session, token: str | None) -> None:
    if token and len(token) <= 100:
        session.execute(delete(LoginSession).where(
            LoginSession.token_hash == _hash_token(token)))
        session.commit()


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
class LoginLimiter:
    """Counts wrong passwords across everyone, not per address.

    Behind Tailscale Serve every request arrives from the same proxy address,
    so a per-IP limit would see one "client" anyway. With a single user, a
    global limit is simplest and strictest: at most MAX_FAILURES guesses per
    LOCKOUT. The cost is that a guesser on the tailnet could keep me locked
    out, which would itself be a loud alarm.

    Kept in memory: a restart clears it, which is fine for one process.
    """

    MAX_FAILURES = 5
    WINDOW = 15 * 60    # seconds
    LOCKOUT = 15 * 60   # seconds

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._failures: deque[float] = deque()
        self._locked_until = 0.0
        self._lock = threading.Lock()

    def seconds_locked(self) -> int:
        """0 if login is allowed, otherwise how long until it is."""
        with self._lock:
            return max(0, int(self._locked_until - self._clock() + 0.999))

    def record_failure(self) -> None:
        with self._lock:
            now = self._clock()
            self._failures.append(now)
            while self._failures and self._failures[0] <= now - self.WINDOW:
                self._failures.popleft()
            if len(self._failures) >= self.MAX_FAILURES:
                self._locked_until = now + self.LOCKOUT
                self._failures.clear()

    def record_success(self) -> None:
        with self._lock:
            self._failures.clear()


limiter = LoginLimiter()
