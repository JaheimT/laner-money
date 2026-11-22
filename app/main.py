"""Laner Money web app: routes, CSRF protection and security headers.

Run (development, from the repo root):
    LANER_ENV=dev .venv/bin/uvicorn app.main:app --host 127.0.0.1

Run (normal use): the same without LANER_ENV=dev. Never use --reload or
--host 0.0.0.0 outside development; binding beyond localhost waits for login.
"""

import datetime
import os
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CATEGORY_MAX, NOTE_MAX, Transaction, get_session
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
    # Secure=False because the app is plain HTTP on localhost for now. When it
    # moves behind HTTPS (M-deployment), this must become secure=True.
    response.set_cookie(CSRF_COOKIE, token, httponly=True, samesite="strict", secure=False)


def csrf_ok(request: Request, form_token: str) -> bool:
    cookie = request.cookies.get(CSRF_COOKIE, "")
    return bool(cookie) and secrets.compare_digest(cookie, form_token)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def render_index(request: Request, session: Session, *, errors=None, form=None,
                 status_code: int = 200) -> HTMLResponse:
    transactions = session.scalars(
        select(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc()).limit(500)
    ).all()
    token = csrf_token_for(request)
    response = templates.TemplateResponse(
        request,
        "index.html",
        {
            "transactions": transactions,
            "balance_pence": sum(t.amount_pence for t in transactions),
            "errors": errors or {},
            "form": form or {"kind": "expense", "date": datetime.date.today().isoformat()},
            "csrf_token": token,
            "category_max": CATEGORY_MAX,
            "note_max": NOTE_MAX,
        },
        status_code=status_code,
    )
    set_csrf_cookie(response, token)
    return response


@app.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(get_session)):
    return render_index(request, session)


@app.post("/transactions")
def add_transaction(
    request: Request,
    session: Session = Depends(get_session),
    # max_length here is a first, coarse limit; validation.py applies the real rules.
    kind: str = Form("", max_length=10),
    amount: str = Form("", max_length=20),
    category: str = Form("", max_length=200),
    note: str = Form("", max_length=1000),
    date: str = Form("", max_length=20),
    csrf_token: str = Form("", max_length=100),
):
    if not csrf_ok(request, csrf_token):
        return PlainTextResponse("Invalid form token. Reload the page and try again.",
                                 status_code=403)

    clean, errors = validate_transaction(kind, amount, category, note, date)
    if errors:
        form = {"kind": kind, "amount": amount, "category": category, "note": note, "date": date}
        return render_index(request, session, errors=errors, form=form, status_code=400)

    session.add(Transaction(**vars(clean)))
    session.commit()
    # Post/Redirect/Get: refreshing the page won't resubmit the form.
    return RedirectResponse("/", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok"}
