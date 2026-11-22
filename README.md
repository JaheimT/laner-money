# Laner Money

*Your money, your server, your rules.*

A self-hosted personal finance app for my homelab, built in Python.

## What this is

Laner Money is a lightweight, self-hosted personal finance app: track
transactions, see where the money goes, and keep the data on my own
hardware. It runs in an LXC container on a Proxmox homelab, reachable over
the LAN and Tailscale only, never the public internet.

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
- **Network:** binds to `127.0.0.1` for now. LAN/Tailscale access waits until
  there's a login.

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

Then open <http://127.0.0.1:8000>.

| Environment variable | Default | Meaning |
|---|---|---|
| `LANER_DB_PATH` | `data/laner.db` | Where the SQLite file lives |
| `LANER_ENV` | *(unset)* | `dev` turns on the API docs pages |

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

## Project layout

```
app/
  main.py        — routes, CSRF, security headers
  models.py      — database setup and the Transaction model
  validation.py  — form input rules
  templates/     — Jinja2 HTML
  static/        — CSS
tests/           — pytest tests
docs/decisions/  — architecture decision records: why we chose what we chose
data/            — SQLite database at runtime (gitignored)
archive/         — retired code (the C version), kept for history
```

## License

MIT, see `LICENSE`.
