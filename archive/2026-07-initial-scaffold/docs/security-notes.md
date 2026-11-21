# Security notes

A running log of security-relevant decisions, known risks, and mitigations.
This is part of the portfolio value of the project — it shows security
thinking applied, not just claimed.

## Threat model (initial)

- **Deployment context:** self-hosted on a home server, typically behind
  a home network / reverse proxy, single-user or small trusted group.
- **Primary assets:** financial transaction data stored in SQLite.
- **Primary risks:**
  - Memory-safety bugs in the hand-rolled HTTP parser (buffer overflows,
    out-of-bounds reads on malformed requests)
  - Injection (SQL injection via unsanitized input into SQLite queries)
  - Auth/session handling (session fixation, weak session tokens, missing
    CSRF protection on state-changing routes)
  - Malformed/oversized HTTP requests (resource exhaustion, parser
    confusion)

## Conventions

- No `strcpy`, `strcat`, `gets`, `sprintf` (unbounded) — use bounded
  equivalents (`strncpy` with explicit null-termination checks, `snprintf`).
- All SQLite queries use parameterized statements (`sqlite3_bind_*`) — no
  string-concatenated SQL, ever.
- All buffer sizes are checked explicitly before writes; no assumptions
  about caller-provided lengths.
- HTTP request parsing treats all input as untrusted: enforce max header
  count, max header size, max body size, before any parsing logic runs.

## Log

(Entries added as decisions are made — format: date, issue, resolution.)
