import datetime

import pytest
from sqlalchemy import delete

from app import budget
from app.db import SessionLocal
from app.models import CategoryBudget, ExcludedCategory, SpendingBudget, Transaction
from app.validation import validate_budget
from tests.conftest import csrf_from

d = datetime.date
TODAY = d(2032, 6, 16)   # a Wednesday, far from other tests' data


@pytest.fixture(autouse=True)
def no_budgets():
    """The test database is shared, so start every test with no budgets."""
    with SessionLocal() as s:
        for table in (SpendingBudget, CategoryBudget, ExcludedCategory):
            s.execute(delete(table))
        s.commit()


# ---------------------------------------------------------------------------
# The maths
# ---------------------------------------------------------------------------
def test_period_bounds():
    assert budget.period_bounds("week", TODAY) == (d(2032, 6, 14), d(2032, 6, 20))
    assert budget.period_bounds("month", TODAY) == (d(2032, 6, 1), d(2032, 6, 30))
    assert budget.period_bounds("month", d(2032, 2, 10)) == (d(2032, 2, 1), d(2032, 2, 29))


def status(spent, amount=8000, days_left=5):
    return budget.BudgetStatus("X", amount, "week", TODAY, TODAY, spent, days_left)


def test_states_and_left():
    assert status(4000).state == "good"
    assert status(6799).state == "good"
    assert status(6800).state == "warn"          # 85% used: nearly full
    assert status(8000).state == "warn"          # exactly used up, not over
    over = status(8400)
    assert over.state == "bad" and over.left_pence == -400 and over.bar_percent == 100


def test_per_day():
    assert status(3000, days_left=5).per_day_pence == 1000
    assert status(8000).per_day_pence == 0       # nothing left
    assert status(9000).per_day_pence == 0       # over


def test_overview_counts_the_right_spending():
    with SessionLocal() as s:
        s.add_all([
            Transaction(amount_pence=-2000, category="Groceries", date=d(2032, 6, 14)),
            Transaction(amount_pence=-1000, category="Eating out", date=d(2032, 6, 15)),
            Transaction(amount_pence=-90000, category="Rent", date=d(2032, 6, 16)),
            Transaction(amount_pence=150000, category="Salary", date=d(2032, 6, 16)),   # income
            Transaction(amount_pence=-5000, category="Groceries", date=d(2032, 6, 13)),  # last week
        ])
        s.commit()
        budget.set_spending_budget(s, 8000, "week")
        budget.set_category_budget(s, "Groceries", 20000, "month")
        budget.set_counts(s, "Rent", counts=False)

        o = budget.overview(s, TODAY)
    # Week: groceries + eating out; Rent switched off; income and last week ignored.
    assert o.spending.spent_pence == 3000 and o.spending.left_pence == 5000
    assert o.spending.days_left == 5 and o.spending.per_day_pence == 1000
    # The groceries limit is monthly, so last week's £50 (still June) counts.
    (groceries,) = o.categories
    assert groceries.spent_pence == 7000 and groceries.period == "month"


def test_category_budget_add_then_change_and_matching_spelling():
    with SessionLocal() as s:
        s.add(Transaction(amount_pence=-100, category="Coffee", date=TODAY))
        s.commit()
        budget.set_category_budget(s, "coffee", 1500, "week")   # typed lower case
        budget.set_category_budget(s, "Coffee", 2000, "month")  # same category: changes it
        (only,) = budget.overview(s, TODAY).categories
    assert (only.name, only.amount_pence, only.period) == ("Coffee", 2000, "month")


def test_counts_toggle():
    with SessionLocal() as s:
        budget.set_counts(s, "Rent", counts=False)
        budget.set_counts(s, "Rent", counts=False)   # twice is fine
        assert budget.excluded_categories(s) == {"Rent"}
        budget.set_counts(s, "Rent", counts=True)
        assert budget.excluded_categories(s) == set()


def test_validate_budget():
    clean, errors = validate_budget("80", "week")
    assert errors == {} and clean == {"amount_pence": 8000, "period": "week"}
    clean, errors = validate_budget("0", "fortnight", "<b>")
    assert clean is None and set(errors) == {"amount", "period", "category"}


# ---------------------------------------------------------------------------
# The pages
# ---------------------------------------------------------------------------
def post(client, url, **data):
    data.setdefault("csrf_token", csrf_from(client.get("/budget/edit").text))
    return client.post(url, data=data, follow_redirects=False)


def test_empty_budget_invites_you_to_set_one(client):
    assert "No budget yet" in client.get("/budget").text
    assert "Set your budget" in client.get("/").text


def test_set_and_remove_spending_budget(client):
    r = post(client, "/budget/spending", amount="65", period="week")
    assert r.status_code == 303 and r.headers["location"] == "/budget/edit#spending"
    page = client.get("/budget").text
    assert "left" in page and "of £65.00 this week" in page
    assert "Budget: this week" in client.get("/").text

    post(client, "/budget/spending/delete")
    assert "No budget yet" in client.get("/budget").text


def test_bad_budget_amount_shows_error(client):
    r = post(client, "/budget/spending", amount="-5", period="week")
    assert r.status_code == 400 and "Amount must be" in r.text
    r = post(client, "/budget/limits", category="", amount="5", period="year")
    assert r.status_code == 400 and "Category is required" in r.text and "week or a month" in r.text


def test_add_change_and_remove_category_limit(client):
    post(client, "/budget/limits", category="Eating out", amount="30", period="week")
    post(client, "/budget/limits", category="Eating out", amount="40", period="week")
    page = client.get("/budget").text
    assert "Eating out" in page and "/ £40.00" in page and "/ £30.00" not in page

    with SessionLocal() as s:
        (limit,) = budget.overview(s).categories
    r = post(client, f"/budget/limits/{limit.id}/delete")
    assert r.status_code == 303
    assert post(client, f"/budget/limits/{limit.id}/delete").status_code == 404


def test_switch_category_off_and_on(client):
    post(client, "/budget/counts", category="Rent", counts="0")
    with SessionLocal() as s:
        assert budget.excluded_categories(s) == {"Rent"}
    assert post(client, "/budget/counts", category="Rent", counts="x").status_code == 400
    post(client, "/budget/counts", category="Rent", counts="1")
    with SessionLocal() as s:
        assert budget.excluded_categories(s) == set()


def test_budget_forms_need_csrf(client):
    for url, data in [("/budget/spending", {"amount": "5", "period": "week"}),
                      ("/budget/spending/delete", {}),
                      ("/budget/limits", {"category": "X", "amount": "5", "period": "week"}),
                      ("/budget/limits/1/delete", {}),
                      ("/budget/counts", {"category": "X", "counts": "0"})]:
        assert post(client, url, csrf_token="nope", **data).status_code == 403, url
