# Archive

Retired code and docs, kept for history rather than deleted.
Nothing in here is built or maintained.

| Folder | What it was | Why retired |
|---|---|---|
| `2026-07-initial-scaffold/` | First scaffold (CMake, hello-world `main.c`, early docs), written on Windows/WSL in July 2026 | Superseded by a fresh start — see `2026-11-c-version/docs/decisions/0001-fresh-start.md` |
| `2026-11-c-version/` | The C rewrite (CMake, ASan/UBSan, `parse_pence` + tests, roadmap, ADRs 0001–0002), November 2026 | Replaced by Python so the app is usable sooner — see `docs/decisions/0003-switch-to-python.md`. Build it from inside that folder with `cmake -S . -B build` |

`git log --follow <path>` still traces each file back to its original location.
