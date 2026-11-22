# Roadmap

Work ONE milestone at a time, in order. Do not start a later milestone or
build features from it. Stop after each numbered step so I can review.
Later milestones must stay possible, but don't build for them yet.

Security passes are their own milestones (M4, M8, M11) so hardening is
never squeezed in "at the end".

**v1** = M0–M11: cash accounts, transactions, pots, balance history, web UI,
deployed on the homelab. **v2** (after M11): net worth, assets and
liabilities (good vs bad debt).

---

## M0 — Toolchain ✅
C, CMake, SQLite, ASan/UBSan in Debug builds. Fresh start Nov 2026 (ADR-0001).

## M1 — HTTP server + transactions (CURRENT)
1. ADR-0002: why we build the HTTP server before a CLI.
2. `parse_pence` (src/core/money.c, include/money.h) + tests/test_money.c.
   I wrote this — check it, don't rewrite it.
3. CMake: src/core + src/db as a static library; `laner` and the tests
   link it; tests run with `ctest`.
4. DB layer (src/db): open DB, create `transactions` table:
   id INTEGER PRIMARY KEY, amount_pence INTEGER NOT NULL, category TEXT
   NOT NULL, note TEXT, date TEXT NOT NULL (ISO 8601).
   Use PRAGMA user_version for schema versioning.
5. Insert + list functions. Prepared statements ONLY — never build SQL
   with string formatting.
6. Minimal HTTP server (replaces the CLI): hand-rolled over raw sockets,
   no libraries. Single-threaded, binds to 127.0.0.1 only, GET only.
   Routes: `GET /health`, then `GET /transactions` (read-only list).
   Cap request size from day one. No POST yet — test data goes in via
   tests or the `sqlite3` tool.
7. DB tests using an in-memory database (":memory:").

## M2 — Pots
Spending (£80/week), Emergency Fund, ISA, Sinking Funds with targets.
Assign transactions to pots; show balance vs target. Still read-only
over HTTP; writes via tests / `sqlite3` until M5.
Schema change goes through user_version migration.

## M3 — (merged into M1 step 6)
The minimal HTTP server moved into M1 (ADR-0002). Number kept so later
milestone references stay stable.

## M4 — Security pass 1: HTTP hardening
Request size limits (line, header count, header size, body), read
timeouts, strict parser that rejects anything malformed. Parser built
so it can be tested in isolation, then fuzzed (Python scripts and/or
libFuzzer/AFL++). Document findings in docs/security-notes.md.

## M5 — JSON API
Read and write routes for transactions and pots. Validate all input in
src/core (amount via parse_pence; category/note length and allowed
characters) so any future interface reuses the same rules. Safe JSON
output encoding. Still localhost only.

## M6 — Accounts + balance history
Cash accounts and manual balance snapshots over time. Completes the v1
data model.

## M7 — Static UI
HTML/CSS in the solarpunk palette (moss, ochre, bark, sand; violet only
for security/trust states). Served by our server, read-only views.
Mockups can be built any time; wiring to live data waits for auth.

## M8 — Security pass 2: auth + sessions
Single-user app password, hashed with an established library (e.g.
libsodium Argon2id — no hand-rolled crypto). Session cookies (random
token, HttpOnly, SameSite=Strict, Secure), CSRF protection on every
state-changing route, login rate limiting.

## M9 — Full UI wiring
Forms for adding/editing transactions, pots and balances, behind auth.

## M10 — Deployment
Release build as a systemd service in an unprivileged LXC on Proxmox,
reached over LAN + VPN only. Dedicated service user, DB file 0600,
automated SQLite backups, logging, update procedure.

## M11 — Security pass 3: full audit
Re-read every module against docs/security-notes.md, refresh the threat
model, re-run fuzzing, static analysis (clang-tidy, cppcheck), and a
portfolio write-up of what was found and fixed.
