# Laner Money

*Your money, your server, your rules.*

A self-hosted personal finance app for my homelab, built in Python.

## What this is

Laner Money is a lightweight, self-hosted personal finance app: track
transactions, see where the money goes, and keep the data on my own
hardware. It runs in Docker on my homelab, reachable over Tailscale only
(HTTPS via Tailscale Serve), never the public internet. See
[docs/deploy.md](docs/deploy.md).

It started life in C with a hand-rolled HTTP server (see `archive/` and
`docs/decisions/0003-switch-to-python.md`). It's now Python, so it's usable
sooner. The security mindset came across unchanged.

## Goals (priority order)

1. **Usable first, learning second.** Something I actually use every week,
   as soon as possible.
2. Build real-world security engineering skills: secure coding practice,
   not just theory.
3. A portfolio piece that shows a real, deployed, secure app.
4. Keep it small enough to self-host easily and extend long-term.

## Stack

| Part | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Fast to build in; 3.11 is what Debian 12 LXC templates ship. |
| Web framework | FastAPI + Uvicorn | Small, typed, well documented, with form handling built in. |
| Database | SQLite via SQLAlchemy ORM | One file, no server process, easy backups. The ORM means no hand-built SQL. |
| Templates | Jinja2 (server-rendered HTML) | No JavaScript build step; autoescaping on by default. |
| Forms | python-multipart | Required by FastAPI to read HTML form posts. |
| Migrations | Alembic | Schema changes without losing data. Run automatically on start. |
| Passwords | argon2-cffi (Argon2id) | Standard, memory-hard password hashing. |

## Security from day one

- **SQL:** only through the SQLAlchemy ORM, which sends values as bound
  parameters. No SQL is ever built from strings.
- **Input:** every field is validated and length-limited (`app/validation.py`).
  Request bodies are capped at 10 KB.
- **CSRF:** every form carries a random token that must match a cookie.
- **Output:** Jinja2 autoescaping, plus a strict Content-Security-Policy.
- **Money:** stored as integer pence and parsed with `Decimal`, never float.
- **Data file:** `data/laner.db` is created with mode `0600`.
- **No debug in production:** API docs only exist with `LANER_ENV=dev`. Never
  run with `--reload` outside development.
- **No secrets in code:** configuration comes from environment variables.
- **Login:** one password, Argon2id-hashed, set by a command. Sessions are
  random tokens (only their SHA-256 is stored) in HttpOnly, Secure,
  SameSite=Strict cookies that expire after 14 days. 5 wrong passwords
  lock login for 15 minutes. Every page except login needs a session (a
  test checks this).
- **Network:** the container binds to `127.0.0.1`; Tailscale Serve adds
  HTTPS for the tailnet. Never public.
- **Container:** non-root user, read-only filesystem, no capabilities.

## Design language

Solarpunk-influenced: earth tones (moss green, ochre, bark brown, sand),
with violet reserved specifically for security/trust states (encryption,
auth, locks, sessions).

## Setup

Needs Python 3.11 or newer.

```bash
# Arch
sudo pacman -S --needed python
# Debian / Ubuntu
sudo apt install python3 python3-venv

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt        # add -dev to run the tests
```

## Running

From the repo root:

```bash
# Development (enables /docs)
LANER_ENV=dev .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Normal use
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Set a password once (`.venv/bin/python -m app.cli set-password`), then open
<http://localhost:8000>. Use `localhost`: the cookies are `Secure`, and
browsers only allow that over plain HTTP on localhost.

| Environment variable | Default | Meaning |
|---|---|---|
| `LANER_DB_PATH` | `data/laner.db` | Where the SQLite file lives |
| `LANER_ENV` | *(unset)* | `dev` turns on the API docs pages |
| `LANER_BACKUP_DIR` | `backups` | Where `python -m app.backup` writes |
| `BACKUP_KEEP` / `BACKUP_HOUR` | `14` / `3` | Backups to keep; nightly hour |

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

## Project layout

```
app/
  main.py        — routes, login check, CSRF, security headers
  auth.py        — password hashing, sessions, login rate limit
  db.py          — database connection, migrations on start-up
  models.py      — the database tables
  reports.py     — dashboard / monthly numbers
  validation.py  — form input rules
  cli.py         — `python -m app.cli set-password`
  backup.py      — `python -m app.backup [--loop]`
  migrations/    — Alembic migration files
  templates/     — Jinja2 HTML
  static/        — CSS
Dockerfile, docker-compose.yml, .env.example — homelab deploy
tests/           — pytest tests
docs/decisions/  — architecture decision records: why we chose what we chose
data/            — SQLite database at runtime (gitignored)
archive/         — retired code (the C version), kept for history
```

## License

MIT, see `LICENSE`.
