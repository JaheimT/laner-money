# ADR 0003: Switch from C to Python

**Status:** Accepted
**Date:** 2026-11-22

ADRs 0001 and 0002 were about the C version. They now live in
`archive/2026-11-c-version/docs/decisions/` and the numbering carries on
from them.

## Context

Laner Money began in C, with a hand-rolled HTTP server, as a way to learn
C, systems programming and secure coding the hard way. After restarting
it in November 2026 I had a toolchain and a tested money parser, but
nothing I could use. On the roadmap, a usable app with a web UI and a login
was at least eight milestones away.

What I want most right now is a finance app I can actually use on my
homelab. I still care about learning security, but not at the cost of
months before the app is usable.

## Options considered

1. **Keep going in C**
   - Pros: deepest learning (memory, sockets, HTTP parsing); fits the
     original goal; work already done carries on.
   - Cons: months before it's usable; every feature costs far more; the
     hardest security problems (an HTTP parser exposed to a network) come
     before anything useful exists.
2. **Python + FastAPI + SQLite**
   - Pros: usable in days; mature, well-tested libraries do HTTP parsing,
     form handling and SQL escaping; easy to deploy in an LXC; still lets me
     practise security where most real bugs are (input validation, auth,
     sessions, CSRF, deployment).
   - Cons: less low-level learning; more dependencies to keep updated;
     slower and heavier than a C binary (doesn't matter for one user).
3. **Use an existing app** (e.g. Firefly III, Actual Budget)
   - Pros: usable today.
   - Cons: not mine to shape; no portfolio piece; teaches me nothing about
     building secure software.

## Decision

**Option 2: Python with FastAPI, SQLAlchemy and Jinja2.**

The priority is now **usable first, learning second**. Python gets me a
working app quickly, and the security work moves to the layers most web
apps get wrong: validation, auth, sessions, CSRF and deployment
hardening. Server-rendered HTML keeps it simple: no JavaScript framework
or build step.

The C code isn't deleted. It's in `archive/2026-11-c-version/` with its
full git history, if I want to come back to it for uni or for fun.

## Security implications

- **Less attack surface written by me:** HTTP parsing is now done by
  Uvicorn/h11, which are widely used and fuzzed, instead of my own parser.
- **SQL injection:** all queries go through the SQLAlchemy ORM (bound
  parameters). No raw SQL strings built from input.
- **New risk: dependencies.** Versions are pinned in `requirements.txt`;
  I need to update them deliberately and watch for security advisories.
- **Web risks still mine to handle:** CSRF (token from day one), XSS
  (Jinja2 autoescaping + Content-Security-Policy), input validation and
  length limits, and later auth and sessions.
- **No debug in production:** API docs only with `LANER_ENV=dev`, no
  `--reload`, bound to 127.0.0.1 until a login exists. Deployment target
  is LAN/Tailscale only, never public.

## Consequences

- **Easier:** features take hours instead of weeks; the app is usable
  after Step 0.
- **Harder:** less practice with C and memory safety on this project; more
  third-party code to trust and keep updated.
- The C roadmap is archived; a new Python roadmap is needed.
- The README's goals are reordered: usability first.
- Schema changes need a migration tool (e.g. Alembic) once there's real
  data, because `create_all` won't alter existing tables.
