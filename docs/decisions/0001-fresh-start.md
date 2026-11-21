# ADR 0001: Fresh start — rebuild the scaffold instead of migrating it

**Status:** Accepted
**Date:** 2026-11-21

## Context

The first scaffold was written in July 2026 on Windows (WSL, VS Code
remote) and then left for about five months. In that time:

- I moved to a new machine running Arch Linux.
- I built a homelab (a Proxmox server), so the deployment target is now
  concrete: one binary plus one SQLite file, probably in an LXC container.
- I learned more C and secure coding at uni, so parts of the old scaffold
  no longer read like code I'd write now.

The old scaffold was small: two commits, a CMake file, a hello-world
`main.c`, and some early docs. **It wasn't broken.** It had no
Windows-only APIs, it used LF line endings, and it still built on Linux.
So the question wasn't "can it be ported?" but "is it better to carry it
forward or to rebuild it?"

The project's goals, in priority order, are: learn C properly, practise
secure coding, build a portfolio piece, and end up with a tool I use. That
makes learning value the main factor, not only engineering cost.

## Options considered

1. **Migrate in place.** Keep the existing files and fix them up
   (link SQLite, add `.gitignore`, create folders).
   - Pros: least work; unbroken file history at the original paths.
   - Cons: I inherit choices I can't fully explain anymore; the
     "why" behind each line is five months stale.
2. **Fresh start, archive the old code.** Move everything except
   `README.md` and `LICENSE` into `archive/`, then rebuild the scaffold
   from scratch.
   - Pros: I rebuild it knowing what every line does, which is my own
     "rebuild it from memory" practice applied to the scaffold; the setup
     is designed for the deployment target I now have; history stays
     visible in `archive/` and in git (`git log --follow`).
   - Cons: a bit of churn in the commit history; some files exist in two
     places (e.g. the ADR template was copied back out of the archive).
3. **Fresh start, delete the old code** (or start a new repo).
   - Pros: the cleanest tree.
   - Cons: loses the record of where the project started, which is part
     of the portfolio story; deleting things doesn't show good judgement
     to a reviewer.

## Decision

**Option 2.** The old code is cheap to replace, since there's almost
nothing to lose. Rebuilding it is a better learning exercise than
patching it. Archiving keeps the history honest: anyone reading the repo
can see what existed before and why it was replaced.

What carried over unchanged: `README.md` (goals, stack, layout), `LICENSE`
and the ADR template. The approach of the old CMake warning flags carried
over too, but it was rewritten and extended rather than copied.

## Security implications

The rebuild was used to set safer defaults from the first commit:

- Debug is the default build type, so AddressSanitizer and
  UndefinedBehaviorSanitizer are on unless Release is explicitly asked
  for.
- Release builds are hardened (`_FORTIFY_SOURCE=3`, full RELRO,
  non-executable stack, stack protector).
- The database file is created as `0600` (owner-only) via `umask(077)`,
  and opened with `SQLITE_OPEN_NOFOLLOW` so a symlink can't redirect it.
- `.gitignore` excludes every SQLite file, including `-journal`, `-wal`
  and `-shm` side files, so financial data can't be committed by
  accident.

The archived docs (`how-we-work.md`, `security-notes.md`) will be
rewritten when they're next needed. One known correction is due: the old
security notes recommended `strncpy`, which doesn't null-terminate the
destination when the source fills it. The replacement will recommend
`snprintf` with its return value checked for truncation.

## Consequences

- Easier: every file in the active tree was written recently and can be
  explained line by line; the build is Linux-first and LXC-ready.
- Harder: `git blame` on the new files starts at this rebuild; older
  history has to be followed through `archive/`.
- Precedent: future retired code also goes to
  `archive/<date>-<name>/` with an entry in `archive/README.md`,
  rather than being deleted.
