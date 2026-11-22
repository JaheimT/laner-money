# ADR 0002: Build the HTTP server before a CLI

**Status:** Accepted
**Date:** 2026-11-22

## Context

M1 builds the first real parts of Laner Money: money parsing
(`parse_pence`), the SQLite database layer, and functions to insert and
list transactions. I need some way to use that code by hand to see if it
works, not just through unit tests.

The final app is a web UI served by my own hand-rolled HTTP server, so
the question is what comes first. The project is for learning C and
secure coding as much as for tracking money, so the choice should help
me learn, not just finish fastest. I'm also new to sockets and HTTP.

## Options considered

1. **CLI first:** commands like `laner add 12.50 food "lunch"` and
   `laner list`, with the server later.
   - Pros: simplest to build; one new thing at a time (SQLite) instead of
     several; small attack surface (only the local user can send input);
     still lets me practise input validation on command-line arguments.
   - Cons: the CLI isn't the real interface, so some of it would be
     thrown away or sidelined later; typing commands is less pleasant
     than a browser; less to learn about network security early on.

2. **HTTP server first:** build a minimal server now and use it from a
   browser or `curl`.
   - Pros: easiest to use once built; easiest to check things work by
     looking at the results; puts me on the path to the real interface
     straight away; more chances to practise spotting vulnerabilities,
     because a network server has much more attack surface than a CLI.
   - Cons: hardest to build. Sockets, partial reads and parsing HTTP by
     hand all have to work before I can see any data. I'd be learning
     several new things at once, which makes bugs harder to pin down.
     Anything that can reach the port can send it input, and the full
     hardening pass is M4.

3. **Tests only:** no interface until the server exists; core and DB
   code only run from unit tests.
   - Pros: most secure, because there's no untrusted input at all; no
     throwaway code.
   - Cons: I can't try the app by hand; I don't practise validating real
     input; feedback is just test output.

## Decision

I'm going with **option 2: the HTTP server first.**

The web interface is what I'll actually use, so building towards it
from the start keeps me motivated and means I'm not building a CLI I
don't need. Being able to see results in a browser makes it easy to
check things work. And a server gives me real attack surface to study,
which is one of the main reasons I'm doing this project.

I was tempted to go further and build the database and website before
any of the functions, but I've kept to the roadmap order: core and DB
functions first, then a small server on top of them.

To keep the risk of building the server early under control, the M1
server is deliberately small (see below). It replaces both the CLI step
in M1 and the old M3 milestone.

## Security implications

- **Binds to 127.0.0.1 only.** Nothing outside my machine can reach it.
- **GET only, read-only routes** (`/health`, `/transactions`). No route
  accepts data to store, so there's no write path to attack yet.
- **Request size is capped from day one.** I'm not waiting for M4 to
  stop a huge request from using up memory.
- **The HTTP parser handles untrusted input.** Even on localhost, I'll
  treat every byte of a request as hostile. M4 hardens the parser
  properly and fuzzes it.
- **SQL injection:** DB access uses prepared statements only (M1 step 5).
- **Input validation for writes** (amount via `parse_pence`, category and
  note rules) arrives with the write routes in M5.

## Consequences

- **Easier:** I see results in a browser early, and the server code grows
  into the real app instead of being thrown away.
- **Harder:** M1 is bigger and harder than it was, and bugs could be in
  the sockets, the HTTP parsing or the DB layer.
- **No way to add data by hand until M5.** Test data goes in through the
  tests or the `sqlite3` tool.
- **Core and DB functions must not print or exit.** They return error
  codes so the server, and any interface added later, can reuse them.
- **M3 is folded into M1.** Its number is kept so references to later
  milestones (M4, M8, M11) stay the same.
