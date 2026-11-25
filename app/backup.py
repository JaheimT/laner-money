"""SQLite backups.

    python -m app.backup             # one backup now
    python -m app.backup --loop      # one now, then every night at BACKUP_HOUR

Uses SQLite's online backup API, so it's safe while the app is running
(copying the file with `cp` mid-write could give a corrupt copy). Each
backup is integrity-checked; only the newest BACKUP_KEEP are kept.

Settings (environment variables):
    LANER_DB_PATH      database to back up          (default data/laner.db)
    LANER_BACKUP_DIR   where backups go             (default backups)
    BACKUP_KEEP        how many to keep             (default 14)
    BACKUP_HOUR        hour of day for --loop, 0-23 (default 3)
"""

import datetime
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

NAME_RE = re.compile(r"laner-\d{4}-\d{2}-\d{2}T\d{6}\.db")


def backup_once(db_path: Path, backup_dir: Path, keep: int) -> Path:
    if not db_path.exists():
        raise FileNotFoundError(f"No database at {db_path}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / f"laner-{datetime.datetime.now():%Y-%m-%dT%H%M%S}.db"
    tmp = dest.with_suffix(".partial")

    src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    dst = sqlite3.connect(tmp)
    try:
        src.backup(dst)
        result = dst.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        src.close()
        dst.close()
    if result != "ok":
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Backup failed its integrity check: {result}")
    os.chmod(tmp, 0o600)          # financial data: owner only
    tmp.rename(dest)              # only complete, checked backups get a real name

    # Keep the newest `keep`; only ever delete files this script made.
    ours = sorted(p for p in backup_dir.iterdir() if NAME_RE.fullmatch(p.name))
    for old in ours[:-keep] if keep > 0 else []:
        old.unlink()
    return dest


def seconds_until(hour: int, now: datetime.datetime | None = None) -> float:
    now = now or datetime.datetime.now()
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return (target - now).total_seconds()


def main(argv: list[str]) -> int:
    db_path = Path(os.environ.get("LANER_DB_PATH", "data/laner.db"))
    backup_dir = Path(os.environ.get("LANER_BACKUP_DIR", "backups"))
    keep = int(os.environ.get("BACKUP_KEEP", "14"))
    hour = int(os.environ.get("BACKUP_HOUR", "3"))
    if not 0 <= hour <= 23 or keep < 1:
        print("BACKUP_HOUR must be 0-23 and BACKUP_KEEP at least 1.", file=sys.stderr)
        return 2

    loop = argv == ["--loop"]
    if argv not in ([], ["--loop"]):
        print(__doc__.strip(), file=sys.stderr)
        return 2

    while True:
        try:
            print(f"Backup written: {backup_once(db_path, backup_dir, keep)}", flush=True)
        except Exception as e:  # keep the loop alive; the next night may work
            print(f"BACKUP FAILED: {e}", file=sys.stderr, flush=True)
            if not loop:
                return 1
        if not loop:
            return 0
        time.sleep(seconds_until(hour))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
