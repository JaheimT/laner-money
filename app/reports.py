"""Numbers for the dashboard and transactions pages.

Plain Python over one month of transactions: a month is at most a few
hundred rows, so there's no need for clever SQL yet.
"""

import calendar
import datetime
import re
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Transaction

_MONTH_RE = re.compile(r"([0-9]{4})-([0-9]{2})")


def parse_month(raw: str | None, today: datetime.date | None = None) -> datetime.date:
    """'2026-11' -> date(2026, 11, 1). Anything missing or odd -> this month."""
    today = today or datetime.date.today()
    match = _MONTH_RE.fullmatch(raw or "")
    if match:
        year, month = int(match[1]), int(match[2])
        if 1900 <= year <= 2100 and 1 <= month <= 12:
            return datetime.date(year, month, 1)
    return today.replace(day=1)


def add_months(first: datetime.date, n: int) -> datetime.date:
    index = first.year * 12 + first.month - 1 + n
    return datetime.date(index // 12, index % 12 + 1, 1)


@dataclass
class CategoryTotal:
    name: str
    out_pence: int
    share: float      # of the biggest category, 0..1: used for bar length


@dataclass
class DayGroup:
    date: datetime.date
    total_pence: int
    transactions: list[Transaction]


@dataclass
class MonthSummary:
    first: datetime.date
    transactions: list[Transaction]          # newest first
    in_pence: int = 0
    out_pence: int = 0                       # a positive number
    categories: list[CategoryTotal] = field(default_factory=list)
    daily_out: list[int] = field(default_factory=list)   # index 0 = the 1st
    days_so_far: int = 0                     # days of this month that have happened

    @property
    def net_pence(self) -> int:
        return self.in_pence - self.out_pence

    @property
    def avg_daily_out_pence(self) -> int | None:
        return self.out_pence // self.days_so_far if self.days_so_far else None

    @property
    def label(self) -> str:
        return self.first.strftime("%B %Y")

    @property
    def key(self) -> str:
        return self.first.strftime("%Y-%m")

    def by_day(self) -> list[DayGroup]:
        groups: list[DayGroup] = []
        for t in self.transactions:
            if not groups or groups[-1].date != t.date:
                groups.append(DayGroup(t.date, 0, []))
            groups[-1].total_pence += t.amount_pence
            groups[-1].transactions.append(t)
        return groups


def month_summary(session: Session, first: datetime.date,
                  today: datetime.date | None = None) -> MonthSummary:
    today = today or datetime.date.today()
    after = add_months(first, 1)
    rows = session.scalars(
        select(Transaction)
        .where(Transaction.date >= first, Transaction.date < after)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
    ).all()

    days_in_month = calendar.monthrange(first.year, first.month)[1]
    summary = MonthSummary(first=first, transactions=list(rows),
                           daily_out=[0] * days_in_month)
    by_category: dict[str, int] = {}
    for t in rows:
        if t.amount_pence > 0:
            summary.in_pence += t.amount_pence
        else:
            spent = -t.amount_pence
            summary.out_pence += spent
            by_category[t.category] = by_category.get(t.category, 0) + spent
            summary.daily_out[t.date.day - 1] += spent

    biggest = max(by_category.values(), default=0)
    summary.categories = [
        CategoryTotal(name, pence, pence / biggest if biggest else 0)
        for name, pence in sorted(by_category.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    if after <= today:
        summary.days_so_far = days_in_month
    elif first <= today:
        summary.days_so_far = today.day
    return summary


def recent_transactions(session: Session, limit: int = 8) -> list[Transaction]:
    return list(session.scalars(
        select(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc()).limit(limit)
    ))


def used_categories(session: Session, limit: int = 100) -> list[str]:
    """Categories already used, most recent first: suggestions for the add form."""
    rows = session.execute(
        select(Transaction.category).group_by(Transaction.category)
        .order_by(func.max(Transaction.id).desc()).limit(limit)
    ).scalars().all()
    return list(rows)
