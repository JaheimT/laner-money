import datetime

import pytest

from app.validation import (MAX_PENCE, parse_amount, parse_category, parse_date,
                            parse_note, validate_transaction)


@pytest.mark.parametrize("raw, pence", [
    ("12", 1200), ("12.5", 1250), ("12.50", 1250), ("0.01", 1),
    (" 3.20 ", 320), ("1000000", MAX_PENCE),
])
def test_amount_ok(raw, pence):
    assert parse_amount(raw) == pence


@pytest.mark.parametrize("raw", [
    "", "0", "0.00", "-5", "+5", "12.345", "12.", ".5", "1,000", "1e3",
    "£5", "NaN", "inf", "1000000.01", "12abc", "١٢",
])
def test_amount_rejected(raw):
    with pytest.raises(ValueError):
        parse_amount(raw)


def test_category():
    assert parse_category("  Eating   out ") == "Eating out"
    assert parse_category("Rock & Roll") == "Rock & Roll"
    assert parse_category("tab\there") == "tab here"   # whitespace normalised
    for bad in ["", "   ", "<script>", "a" * 51, "x;DROP TABLE", "-dash", "_x"]:
        with pytest.raises(ValueError):
            parse_category(bad)


def test_note():
    assert parse_note("   ") is None
    assert parse_note(" lunch with Sam ") == "lunch with Sam"
    for bad in ["a" * 201, "line\nbreak", "nul\x00"]:
        with pytest.raises(ValueError):
            parse_note(bad)


def test_date():
    today = datetime.date(2026, 11, 22)
    assert parse_date("2026-11-22", today) == today
    for bad in ["", "2026-02-30", "22/11/2026", "2028-01-01", "1800-01-01"]:
        with pytest.raises(ValueError):
            parse_date(bad, today)


def test_expense_is_negative_and_errors_collected():
    clean, errors = validate_transaction("expense", "4.20", "Coffee", "", "2026-11-22")
    assert errors == {} and clean.amount_pence == -420 and clean.note is None
    clean, errors = validate_transaction("gift", "x", "", "", "nope")
    assert clean is None and set(errors) == {"kind", "amount", "category", "date"}
