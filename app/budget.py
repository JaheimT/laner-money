"""Budgets: the amounts the user sets, and how much of each is used.

- One optional overall spending budget (amount + week or month). It counts
  every expense except categories marked "doesn't count" (e.g. Rent).
- Optional limits per category, each with its own amount and period.
- Weeks run Monday to Sunday; months are calendar months.
"""

import calendar
import datetime
from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import CategoryBudget, ExcludedCategory, SpendingBudget, Transaction

NEARLY_FULL = 0.85   # used this much or more: "Nearly full"


def period_bounds(period: str, today: datetime.date) -> tuple[datetime.date, datetime.date]:
    """First and last day (inclusive) of the week or month containing today."""
    if period == "week":
        start = today - datetime.timedelta(days=today.weekday())
        return start, start + datetime.timedelta(days=6)
    last = calendar.monthrange(today.year, today.month)[1]
    return today.replace(day=1), today.replace(day=last)


@dataclass
class BudgetStatus:
    name: str
    amount_pence: int
    period: str
    start: datetime.date
    end: datetime.date
    spent_pence: int
    days_left: int                    # including today
    id: int | None = None             # category budget id; None for the overall one

    @property
    def left_pence(self) -> int:
        return self.amount_pence - self.spent_pence

    @property
    def used(self) -> float:
        return self.spent_pence / self.amount_pence

    @property
    def state(self) -> str:
        """good / warn / bad: shown with an icon and a word, never colour alone."""
        if self.spent_pence > self.amount_pence:
            return "bad"
        return "warn" if self.used >= NEARLY_FULL else "good"

    @property
    def per_day_pence(self) -> int:
        """Roughly how much can be spent each remaining day."""
        return self.left_pence // self.days_left if self.left_pence > 0 and self.days_left else 0

    @property
    def bar_percent(self) -> float:
        return min(self.used, 1.0) * 100


@dataclass
class Overview:
    spending: BudgetStatus | None
    categories: list[BudgetStatus]

    @property
    def is_empty(self) -> bool:
        return self.spending is None and not self.categories


def _spent(session: Session, start: datetime.date, end: datetime.date, *,
           category: str | None = None, excluded: set[str] = frozenset()) -> int:
    query = select(func.coalesce(func.sum(Transaction.amount_pence), 0)).where(
        Transaction.date >= start, Transaction.date <= end, Transaction.amount_pence < 0)
    if category is not None:
        query = query.where(Transaction.category == category)
    elif excluded:
        query = query.where(Transaction.category.not_in(excluded))
    return -session.scalar(query)


def _status(session: Session, name: str, amount: int, period: str, today: datetime.date,
            **spent_filter) -> BudgetStatus:
    start, end = period_bounds(period, today)
    return BudgetStatus(name, amount, period, start, end,
                        _spent(session, start, end, **spent_filter), (end - today).days + 1)


def overview(session: Session, today: datetime.date | None = None) -> Overview:
    today = today or datetime.date.today()
    excluded = excluded_categories(session)
    overall = session.get(SpendingBudget, 1)
    spending = (_status(session, "Spending", overall.amount_pence, overall.period, today,
                        excluded=excluded) if overall else None)
    categories = []
    for b in session.scalars(select(CategoryBudget).order_by(CategoryBudget.category)):
        status = _status(session, b.category, b.amount_pence, b.period, today, category=b.category)
        status.id = b.id
        categories.append(status)
    return Overview(spending, categories)


# ---------------------------------------------------------------------------
# Changing budgets
# ---------------------------------------------------------------------------
def get_spending_budget(session: Session) -> SpendingBudget | None:
    return session.get(SpendingBudget, 1)


def set_spending_budget(session: Session, amount_pence: int, period: str) -> None:
    budget = session.get(SpendingBudget, 1) or SpendingBudget(id=1)
    budget.amount_pence, budget.period = amount_pence, period
    session.add(budget)
    session.commit()


def clear_spending_budget(session: Session) -> None:
    session.execute(delete(SpendingBudget))
    session.commit()


def _known_spelling(session: Session, category: str) -> str:
    """Match an existing category ignoring case ('coffee' -> 'Coffee'), so a
    limit always lines up with the transactions it's meant to count."""
    existing = session.scalar(select(Transaction.category).where(
        func.lower(Transaction.category) == category.lower()).limit(1))
    return existing or category


def set_category_budget(session: Session, category: str, amount_pence: int, period: str) -> None:
    """Add a limit, or change it if that category already has one."""
    category = _known_spelling(session, category)
    budget = session.scalar(select(CategoryBudget).where(CategoryBudget.category == category))
    budget = budget or CategoryBudget(category=category)
    budget.amount_pence, budget.period = amount_pence, period
    session.add(budget)
    session.commit()


def delete_category_budget(session: Session, budget_id: int) -> bool:
    budget = session.get(CategoryBudget, budget_id) if 0 < budget_id < 2**63 else None
    if budget is None:
        return False
    session.delete(budget)
    session.commit()
    return True


def excluded_categories(session: Session) -> set[str]:
    return set(session.scalars(select(ExcludedCategory.category)))


def set_counts(session: Session, category: str, counts: bool) -> None:
    """Whether a category counts toward the overall spending budget."""
    row = session.get(ExcludedCategory, category)
    if counts and row:
        session.delete(row)
    elif not counts and not row:
        session.add(ExcludedCategory(category=category))
    session.commit()


def all_categories(session: Session, limit: int = 200) -> list[str]:
    """Every category the budget page should list, alphabetically: ones used in
    transactions, plus any with a limit or marked as not counting."""
    names = set(session.scalars(select(Transaction.category).distinct().limit(limit)))
    names |= set(session.scalars(select(CategoryBudget.category)))
    names |= excluded_categories(session)
    return sorted(names, key=str.lower)
