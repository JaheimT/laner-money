# How this project is built

This file exists so the reasoning behind the project's process is visible —
useful for future-me, and for anyone reading this as a portfolio piece.

## Teaching approach

This project is a learning vehicle first, a shipped product second. Working
sessions on this codebase (with Claude, or notes to self) follow these rules:

1. **Explain the reasoning, not just the fix.** Memory, pointers, protocol
   behavior, security implications — the "why," not just the "what."
2. **Weigh real alternatives.** For any meaningful implementation decision,
   consider multiple approaches with honest tradeoffs before picking one,
   and record *why* the chosen option fits this project specifically.
3. **Flag security issues proactively.** Buffer overflows, integer overflows,
   format string bugs, use-after-free, unsafe string functions
   (`strcpy`/`gets`/etc.), SQL injection, and web-layer risks (malformed or
   malicious HTTP input, header injection, auth/session handling, CSRF) —
   called out even when not directly asked about.
4. **Keep deployability in mind.** Avoid dependencies or patterns that would
   make self-hosting harder, for me or for anyone else running this.
5. **Document as we go.** Meaningful design decisions get an ADR in
   `docs/decisions/`. Commit messages explain *why*, not just *what*.

## Architecture Decision Records (ADRs)

Each significant decision (e.g. "why raw sockets instead of a library",
"why SQLite over Postgres", "how sessions are handled") gets a short
numbered file in `docs/decisions/`, following the template in
`docs/decisions/0000-template.md`.
