# ADR 0004: Global login rate limit, not per device

**Status:** Accepted
**Date:** 2026-11-25

## Context

Laner Money has one user and one password. To slow down password
guessing, login needs a rate limit (roadmap M3 step 3).

On the homelab the app sits behind Tailscale Serve, which passes every
request on from the same local address. From the app's point of view,
every phone and laptop looks like the same client. The app can't
reliably tell devices apart.

## Options considered

1. **Per device (per IP address)**: count wrong passwords for each
   client address.
   - Pros: a guesser can only lock out themselves, not me.
   - Cons: behind Tailscale Serve every request comes from the same
     address, so in practice it's a global limit anyway. Trusting headers
     like `X-Forwarded-For` to tell devices apart adds complexity and a way
     to fake being a "new device".
2. **Global**: count wrong passwords from everyone together.
   - Pros: simple; the strictest limit on guessing (at most 5 guesses per
     15 minutes in total); no dependence on proxy headers.
   - Cons: anyone who can reach the login page can lock me out by typing
     wrong passwords.
3. **No rate limit, rely on Argon2id being slow**
   - Pros: nothing to build.
   - Cons: Argon2id slows each guess but doesn't cap how many guesses
     someone can make; the roadmap requires a limit.

## Decision

Option 2: a global limit. After 5 wrong passwords within 15 minutes,
login is locked for 15 minutes, even for the right password
(`app/auth.py`, `LoginLimiter`).

The trade-off is accepted because the app is only reachable from my
tailnet, which is only my own devices. Anyone who could lock me out would
already be on my tailnet, and a lockout would be a clear warning sign.

## Security implications

- Caps guessing at 5 tries per 15 minutes in total, on top of Argon2id.
- Denial of service: someone on the tailnet can keep login locked. Only
  my devices are on the tailnet, so this is acceptable.
- The counter lives in memory: restarting the container clears it
  (`docker compose restart laner`). An attacker can't restart it, and it's
  how I unlock myself if needed.
- Needs a single app process. Running several uvicorn workers would give
  each its own counter.

## Consequences

- Simple to understand and test.
- Must be revisited if the app ever has more than one user, or is shared
  beyond my own devices (Phase 2): per-user or per-device limits, and a
  limiter stored outside one process's memory.
