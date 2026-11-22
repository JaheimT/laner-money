"""Turn raw form input into clean values, or explain what's wrong.

Kept separate from the routes so the rules can be tested on their own and
reused by any future interface (a JSON API, a CSV import...).
"""

import datetime
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.models import CATEGORY_MAX, NOTE_MAX

MAX_PENCE = 100_000_000  # £1,000,000.00

# ASCII digits, optionally a dot and one or two digits: "12", "12.5", "12.50".
# [0-9], not \d: in Python \d also matches digits from other scripts ("١٢"),
# which Decimal would happily accept.
_AMOUNT_RE = re.compile(r"[0-9]{1,7}(\.[0-9]{1,2})?")
# Starts with a letter or digit (any language); then letters, digits,
# spaces and - & '  only. No markup or SQL punctuation.
_CATEGORY_RE = re.compile(r"[^\W_](?:[^\W_]|[ \-&'])*")


@dataclass
class CleanTransaction:
    amount_pence: int
    category: str
    note: str | None
    date: datetime.date


def parse_amount(raw: str) -> int:
    """'12.50' -> 1250. Raises ValueError with a user-facing message."""
    raw = raw.strip()
    if not _AMOUNT_RE.fullmatch(raw):
        raise ValueError("Amount must be a number like 12 or 12.50 (no £, commas or signs).")
    try:
        pence = int(Decimal(raw) * 100)  # Decimal is exact; float is not
    except InvalidOperation:
        raise ValueError("Amount must be a number like 12 or 12.50.") from None
    if pence <= 0:
        raise ValueError("Amount must be more than zero.")
    if pence > MAX_PENCE:
        raise ValueError("Amount must be £1,000,000 or less.")
    return pence


def parse_category(raw: str) -> str:
    category = " ".join(raw.split())  # trim and collapse runs of whitespace
    if not category:
        raise ValueError("Category is required.")
    if len(category) > CATEGORY_MAX:
        raise ValueError(f"Category must be {CATEGORY_MAX} characters or fewer.")
    if not _CATEGORY_RE.fullmatch(category):
        raise ValueError("Category can only contain letters, numbers, spaces and - & '.")
    return category


def parse_note(raw: str) -> str | None:
    note = raw.strip()
    if not note:
        return None
    if len(note) > NOTE_MAX:
        raise ValueError(f"Note must be {NOTE_MAX} characters or fewer.")
    if any(not ch.isprintable() for ch in note):
        raise ValueError("Note can't contain control characters or line breaks.")
    return note


def parse_date(raw: str, today: datetime.date | None = None) -> datetime.date:
    today = today or datetime.date.today()
    try:
        value = datetime.date.fromisoformat(raw.strip())
    except ValueError:
        raise ValueError("Date must be a real date in the form YYYY-MM-DD.") from None
    if value > today + datetime.timedelta(days=366):
        raise ValueError("Date can't be more than a year in the future.")
    if value.year < 1900:
        raise ValueError("Date is too far in the past.")
    return value


def validate_transaction(
    kind: str, amount: str, category: str, note: str, date: str
) -> tuple[CleanTransaction | None, dict[str, str]]:
    """Validate every field; return (clean value, {}) or (None, errors by field)."""
    errors: dict[str, str] = {}
    values: dict = {}
    for field, parse, raw in (
        ("amount", parse_amount, amount),
        ("category", parse_category, category),
        ("note", parse_note, note),
        ("date", parse_date, date),
    ):
        try:
            values[field] = parse(raw)
        except ValueError as e:
            errors[field] = str(e)

    if kind not in ("expense", "income"):
        errors["kind"] = "Choose expense or income."

    if errors:
        return None, errors

    sign = -1 if kind == "expense" else 1
    return CleanTransaction(
        amount_pence=sign * values["amount"],
        category=values["category"],
        note=values["note"],
        date=values["date"],
    ), {}
