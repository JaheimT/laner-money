# Laner Money

*Your money, your server, your rules.*

A self-hosted personal finance platform, built from scratch in C.

## What this is

Laner Money is a lightweight, self-hosted personal finance app. It's built
deliberately close to the metal: a hand-rolled HTTP server over raw sockets,
SQLite for storage, and no web framework in between. That's not the "easy"
way to build a finance app — it's the point. This project exists to build
real systems and security engineering skills through the friction of doing
things manually, while ending up with something genuinely useful to run
day-to-day on a home server.

## Why it's built this way

| Decision | Reasoning |
|---|---|
| C | Core language requirement for university coursework; also the best way to actually understand memory, pointers, and the cost of abstractions. |
| Hand-rolled HTTP over raw sockets | No framework hiding the parsing, request handling, or attack surface. The HTTP layer *is* part of the security curriculum here. |
| SQLite | Single-file, zero-server-process storage. Minimal deployment footprint, easy backups, easy to self-host. |
| CMake | Standard, portable build tooling that scales as the project grows past a single `gcc` command. |
| Minimal dependencies | Keeps self-hosting realistic for me and for anyone else who wants to run this on their own hardware. |

## Status

Early scaffolding. Not yet functional. See `docs/decisions/` for design
decisions as they're made, and commit history for progress.

## Goals (priority order)

1. Learn C properly, for university and beyond
2. Build real-world security engineering skills — secure coding practice, not just theory
3. Build a portfolio piece that demonstrates real systems work
4. End up with a tool I actually use and can keep extending long-term

## Stack

- **Language:** C
- **Build system:** CMake
- **Storage:** SQLite
- **Web layer:** Hand-rolled HTTP parser/server over raw sockets (no libcurl/libmicrohttpd/etc.)
- **Deployment:** Self-hosted, single binary + single SQLite file, minimal deps

## Design language

Solarpunk-influenced — earth tones (moss green, ochre, bark brown, sand),
with violet reserved specifically for security/trust states (encryption,
auth, locks, sessions).

## Building

Dependencies: a C compiler, CMake ≥ 3.20, SQLite 3.31+ with headers.

```bash
# Arch
sudo pacman -S --needed base-devel cmake sqlite
# Debian / Ubuntu
sudo apt install build-essential cmake libsqlite3-dev
```

Build and run (from the repo root — the database lives at `data/laner.db`):

```bash
cmake -S . -B build          # Debug by default: ASan + UBSan enabled
cmake --build build
./build/laner
```

Release (optimised, hardened, no sanitizers):

```bash
cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release
cmake --build build-release
```

## Project layout

```
src/
  core/     — application logic, models, business rules
  db/       — SQLite access layer
  http/     — hand-rolled HTTP server (sockets, parsing, routing)
include/    — public headers
tests/      — test files
docs/
  decisions/ — architecture decision records (ADRs) — why we chose what we chose
data/       — local SQLite db file lives here at runtime (gitignored)
scripts/    — dev/deploy helper scripts
```

## License

MIT — see `LICENSE`.
