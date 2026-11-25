import datetime
import sqlite3

from app import reports
from app.db import SessionLocal, make_engine
from app.models import Transaction


def test_parse_month():
    today = datetime.date(2026, 11, 25)
    assert reports.parse_month("2024-03", today) == datetime.date(2024, 3, 1)
    for bad in [None, "", "2024-13", "2024-3", "1899-12", "nonsense"]:
        assert reports.parse_month(bad, today) == datetime.date(2026, 11, 1)


def test_add_months():
    d = datetime.date
    assert reports.add_months(d(2026, 12, 1), 1) == d(2027, 1, 1)
    assert reports.add_months(d(2026, 1, 1), -1) == d(2025, 12, 1)


def test_month_summary():
    d = datetime.date
    with SessionLocal() as s:
        s.add_all([
            Transaction(amount_pence=-1000, category="Food", date=d(2025, 2, 3)),
            Transaction(amount_pence=-500, category="Food", date=d(2025, 2, 3)),
            Transaction(amount_pence=-300, category="Bus", date=d(2025, 2, 10)),
            Transaction(amount_pence=200000, category="Salary", date=d(2025, 2, 28)),
            Transaction(amount_pence=-9999, category="Food", date=d(2025, 3, 1)),  # next month
        ])
        s.commit()
        m = reports.month_summary(s, d(2025, 2, 1), today=d(2026, 1, 1))
    assert (m.in_pence, m.out_pence, m.net_pence) == (200000, 1800, 198200)
    assert [(c.name, c.out_pence, c.share) for c in m.categories] == [("Food", 1500, 1.0), ("Bus", 300, 0.2)]
    assert len(m.daily_out) == 28 and m.daily_out[2] == 1500 and m.daily_out[9] == 300
    assert m.days_so_far == 28 and m.avg_daily_out_pence == 1800 // 28
    assert [g.date.day for g in m.by_day()] == [28, 10, 3]


def test_days_so_far_for_current_and_future_month():
    with SessionLocal() as s:
        today = datetime.date(2030, 6, 12)
        assert reports.month_summary(s, datetime.date(2030, 6, 1), today).days_so_far == 12
        assert reports.month_summary(s, datetime.date(2030, 7, 1), today).days_so_far == 0


def test_week_spending_counts_monday_to_sunday_money_out_only():
    d = datetime.date
    with SessionLocal() as s:
        s.add_all([
            Transaction(amount_pence=-111, category="Before", date=d(2031, 3, 2)),   # Sunday before
            Transaction(amount_pence=-200, category="Mon", date=d(2031, 3, 3)),
            Transaction(amount_pence=-300, category="Sun", date=d(2031, 3, 9)),
            Transaction(amount_pence=5000, category="Pay", date=d(2031, 3, 5)),      # income ignored
        ])
        s.commit()
        w = reports.week_spending(s, today=d(2031, 3, 5))   # a Wednesday
    assert (w.start, w.end) == (d(2031, 3, 3), d(2031, 3, 9))
    assert w.out_pence == 500 and w.days_left == 5


def test_month_calendar():
    weeks = reports.month_calendar(datetime.date(2026, 11, 1))   # 1 Nov 2026 is a Sunday
    assert weeks[0] == [None] * 6 + [datetime.date(2026, 11, 1)]
    assert weeks[-1][0] == datetime.date(2026, 11, 30) and weeks[-1][1:] == [None] * 6
    assert all(len(w) == 7 for w in weeks)


def test_tax_year_end():
    d = datetime.date
    assert reports.tax_year_end(d(2026, 11, 25)) == d(2027, 4, 5)
    assert reports.tax_year_end(d(2027, 4, 5)) == d(2027, 4, 5)
    assert reports.tax_year_end(d(2027, 4, 6)) == d(2028, 4, 5)


def test_pre_alembic_database_is_upgraded_in_place(tmp_path):
    """An M0 database (made by create_all, no alembic_version) keeps its data."""
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE transactions (id INTEGER PRIMARY KEY, amount_pence INTEGER NOT NULL,"
                " category VARCHAR(50) NOT NULL, note VARCHAR(200), date DATE NOT NULL)")
    con.execute("INSERT INTO transactions VALUES (1, -420, 'Coffee', NULL, '2026-11-22')")
    con.commit()
    con.close()
    make_engine(path).dispose()
    con = sqlite3.connect(path)
    assert con.execute("SELECT version_num FROM alembic_version").fetchone() == ("0003",)
    assert con.execute("SELECT count(*) FROM transactions").fetchone() == (1,)
    assert con.execute("SELECT count(*) FROM users").fetchone() == (0,)
