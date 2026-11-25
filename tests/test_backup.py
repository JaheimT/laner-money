import datetime
import sqlite3
import stat

from app import backup


def make_db(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE t (x INTEGER)")
    con.execute("INSERT INTO t VALUES (42)")
    con.commit()
    con.close()


def test_backup_copies_data_and_prunes(tmp_path):
    db = tmp_path / "laner.db"
    make_db(db)
    out = tmp_path / "backups"
    out.mkdir()
    for day in range(1, 5):   # pretend older backups exist
        (out / f"laner-2026-01-0{day}T030000.db").write_bytes(b"old")
    (out / "my-notes.txt").write_text("not ours, never deleted")

    made = backup.backup_once(db, out, keep=3)

    assert sqlite3.connect(made).execute("SELECT x FROM t").fetchone() == (42,)
    assert stat.S_IMODE(made.stat().st_mode) == 0o600
    names = sorted(p.name for p in out.iterdir())
    assert names == ["laner-2026-01-03T030000.db", "laner-2026-01-04T030000.db",
                     made.name, "my-notes.txt"]


def test_seconds_until():
    now = datetime.datetime(2026, 11, 25, 22, 0)
    assert backup.seconds_until(3, now) == 5 * 3600
    assert backup.seconds_until(22, now) == 24 * 3600
