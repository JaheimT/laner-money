"""Laner Money web app: routes, login, CSRF protection and security headers.

Run (development, from the repo root):
    LANER_ENV=dev .venv/bin/uvicorn app.main:app --host 127.0.0.1

Open it as http://localhost:8000 (cookies are always Secure; browsers
allow that on localhost only). Never use --reload outside development.
On the homelab it runs in Docker behind Tailscale Serve (HTTPS); see
docs/deploy.md.
"""

import datetime
import os
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import auth, reports
from app.db import get_session
from app.models import CATEGORY_MAX, NOTE_MAX, Transaction
from app.validation import validate_transaction

BASE_DIR = Path(__file__).resolve().parent
DEV = os.environ.get("LANER_ENV") == "dev"

# The auto-generated API docs (/docs, /redoc, /openapi.json) are handy while
# developing but just extra surface otherwise, so they only exist in dev.
app = FastAPI(
    title="Laner Money",
    docs_url="/docs" if DEV else None,
    redoc_url=None,
    openapi_url="/openapi.json" if DEV else None,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
# Jinja2Templates turns on autoescaping for .html files: anything a user typed
# is shown as text, never run as HTML or JavaScript.
templates = Jinja2Templates(directory=BASE_DIR / "templates")

MAX_BODY_BYTES = 10_000  # a transaction form is a few hundred bytes
CSRF_COOKIE = "laner_csrf"


def format_money(pence: int, signed: bool = False) -> str:
    """1234 -> '£12.34'; -1234 -> '−£12.34' (real minus sign, U+2212).
    signed=True also puts '+' on positive amounts."""
    sign = "−" if pence < 0 else ("+" if signed and pence > 0 else "")
    pounds, p = divmod(abs(pence), 100)
    return f"{sign}£{pounds:,}.{p:02d}"


templates.env.globals["money"] = format_money


# ---------------------------------------------------------------------------
# Middleware: body size limit + security headers on every response
# ---------------------------------------------------------------------------
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    length = request.headers.get("content-length")
    if request.method == "POST" and (length is None or not length.isdigit()
                                     or int(length) > MAX_BODY_BYTES):
        return PlainTextResponse("Request too large or missing length.", status_code=413)

    response = await call_next(request)
    # Only load scripts/styles/images from this server; never be framed.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if not request.url.path.startswith("/static/"):
        # Pages show financial data: don't leave copies in browser caches.
        response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------------------------------------------------------
# CSRF: "double submit" token. The page sets a random token in a cookie and
# puts the same token in a hidden form field. Another website can make your
# browser POST here, but it can't read the cookie, so it can't match it.
# ---------------------------------------------------------------------------
def csrf_token_for(request: Request) -> str:
    token = request.cookies.get(CSRF_COOKIE)
    return token if token and len(token) == 43 else secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str) -> None:
    # Secure: only ever sent over HTTPS (Tailscale Serve), or to localhost.
    response.set_cookie(CSRF_COOKIE, token, httponly=True, samesite="strict", secure=True)


def csrf_ok(request: Request, form_token: str) -> bool:
    cookie = request.cookies.get(CSRF_COOKIE, "")
    return bool(cookie) and secrets.compare_digest(cookie, form_token)


def csrf_failed() -> PlainTextResponse:
    return PlainTextResponse("Invalid form token. Reload the page and try again.",
                             status_code=403)


def render(request: Request, template: str, context: dict,
           status_code: int = 200) -> HTMLResponse:
    """Render a page with a CSRF token for its forms."""
    token = csrf_token_for(request)
    response = templates.TemplateResponse(
        request, template, {"csrf_token": token, **context}, status_code=status_code)
    set_csrf_cookie(response, token)
    return response


# ---------------------------------------------------------------------------
# Login required: every route on `protected` checks for a valid session.
# New pages go on `protected` unless they truly must work logged out.
# ---------------------------------------------------------------------------
class LoginRequired(Exception):
    pass


@app.exception_handler(LoginRequired)
def to_login(request: Request, exc: LoginRequired):
    return RedirectResponse("/login", status_code=303)


def require_login(request: Request, session: Session = Depends(get_session)) -> None:
    if not auth.session_is_valid(session, request.cookies.get(auth.SESSION_COOKIE)):
        raise LoginRequired()


protected = APIRouter(dependencies=[Depends(require_login)])


# ---------------------------------------------------------------------------
# Public routes: login and health check
# ---------------------------------------------------------------------------
def render_login(request: Request, session: Session, *, error: str = "",
                 status_code: int = 200) -> HTMLResponse:
    return render(request, "login.html", {
        "error": error,
        "setup_needed": not auth.password_is_set(session),
        "seconds_locked": auth.limiter.seconds_locked(),
        "password_max": auth.PASSWORD_MAX,
    }, status_code=status_code)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, session: Session = Depends(get_session)):
    if auth.session_is_valid(session, request.cookies.get(auth.SESSION_COOKIE)):
        return RedirectResponse("/", status_code=303)
    return render_login(request, session)


@app.post("/login")
def login(
    request: Request,
    session: Session = Depends(get_session),
    password: str = Form("", max_length=auth.PASSWORD_MAX),
    csrf_token: str = Form("", max_length=100),
):
    if not csrf_ok(request, csrf_token):
        return csrf_failed()
    if auth.limiter.seconds_locked():
        return render_login(request, session, status_code=429,
                            error="Too many wrong passwords. Login is locked for now.")
    if not auth.verify_password(session, password):
        auth.limiter.record_failure()
        return render_login(request, session, status_code=401, error="Wrong password.")

    auth.limiter.record_success()
    token = auth.create_session(session)
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(auth.SESSION_COOKIE, token, httponly=True, samesite="strict",
                        secure=True, max_age=int(auth.SESSION_LIFETIME.total_seconds()))
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Logged-in pages
# ---------------------------------------------------------------------------
@protected.post("/logout")
def logout(request: Request, session: Session = Depends(get_session),
           csrf_token: str = Form("", max_length=100)):
    if not csrf_ok(request, csrf_token):
        return csrf_failed()
    auth.end_session(session, request.cookies.get(auth.SESSION_COOKIE))
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(auth.SESSION_COOKIE, httponly=True, samesite="strict", secure=True)
    return response


def month_nav(first: datetime.date) -> dict:
    this_month = datetime.date.today().replace(day=1)
    return {
        "prev_key": reports.add_months(first, -1).strftime("%Y-%m"),
        "next_key": reports.add_months(first, 1).strftime("%Y-%m"),
        "is_current": first == this_month,
    }


@protected.get("/", response_class=HTMLResponse)
def dashboard(request: Request, month: str = "", session: Session = Depends(get_session)):
    first = reports.parse_month(month)
    today = datetime.date.today()
    tax_year_end = reports.tax_year_end(today)
    return render(request, "dashboard.html", {
        "page": "dashboard",
        "summary": reports.month_summary(session, first),
        "recent": reports.recent_transactions(session, limit=5),
        "week": reports.week_spending(session, today),
        "calendar": reports.month_calendar(first),
        "today": today,
        "tax_year_end": tax_year_end,
        "tax_days_left": (tax_year_end - today).days,
        **month_nav(first),
    })


@protected.get("/transactions", response_class=HTMLResponse)
def transactions_page(request: Request, month: str = "",
                      session: Session = Depends(get_session)):
    first = reports.parse_month(month)
    return render(request, "transactions.html", {
        "page": "transactions",
        "summary": reports.month_summary(session, first),
        **month_nav(first),
    })


def render_add(request: Request, session: Session, *, errors=None, form=None,
               saved: bool = False, status_code: int = 200) -> HTMLResponse:
    return render(request, "add.html", {
        "page": "add",
        "errors": errors or {},
        "form": form or {"kind": "expense", "date": datetime.date.today().isoformat()},
        "saved": saved,
        "categories": reports.used_categories(session),
        "category_max": CATEGORY_MAX,
        "note_max": NOTE_MAX,
    }, status_code=status_code)


@protected.get("/add", response_class=HTMLResponse)
def add_page(request: Request, saved: str = "", session: Session = Depends(get_session)):
    return render_add(request, session, saved=saved == "1")


# Where "Save" can send you next. A fixed list, so the form can't be used to
# redirect to another site.
AFTER_SAVE = {"dashboard": "/", "add": "/add?saved=1", "transactions": "/transactions"}


@protected.post("/transactions")
def add_transaction(
    request: Request,
    session: Session = Depends(get_session),
    # max_length here is a first, coarse limit; validation.py applies the real rules.
    kind: str = Form("", max_length=10),
    amount: str = Form("", max_length=20),
    category: str = Form("", max_length=200),
    note: str = Form("", max_length=1000),
    date: str = Form("", max_length=20),
    then: str = Form("dashboard", max_length=20),
    csrf_token: str = Form("", max_length=100),
):
    if not csrf_ok(request, csrf_token):
        return csrf_failed()

    clean, errors = validate_transaction(kind, amount, category, note, date)
    if errors:
        form = {"kind": kind, "amount": amount, "category": category, "note": note, "date": date}
        return render_add(request, session, errors=errors, form=form, status_code=400)

    session.add(Transaction(**vars(clean)))
    session.commit()
    # Post/Redirect/Get: refreshing the page won't resubmit the form.
    return RedirectResponse(AFTER_SAVE.get(then, "/"), status_code=303)


def get_transaction_or_404(session: Session, tx_id: int) -> Transaction | None:
    return session.get(Transaction, tx_id) if 0 < tx_id < 2**63 else None


@protected.get("/transactions/{tx_id}/delete", response_class=HTMLResponse)
def confirm_delete(request: Request, tx_id: int, session: Session = Depends(get_session)):
    tx = get_transaction_or_404(session, tx_id)
    if tx is None:
        return PlainTextResponse("No such transaction.", status_code=404)
    return render(request, "confirm_delete.html", {"page": "transactions", "t": tx})


@protected.post("/transactions/{tx_id}/delete")
def delete_transaction(request: Request, tx_id: int, session: Session = Depends(get_session),
                       csrf_token: str = Form("", max_length=100)):
    if not csrf_ok(request, csrf_token):
        return csrf_failed()
    tx = get_transaction_or_404(session, tx_id)
    if tx is None:
        return PlainTextResponse("No such transaction.", status_code=404)
    month = tx.date.strftime("%Y-%m")
    session.delete(tx)
    session.commit()
    return RedirectResponse(f"/transactions?month={month}", status_code=303)


app.include_router(protected)
