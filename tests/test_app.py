import datetime

from fastapi.routing import APIRoute

from app.main import app, format_money, protected
from tests.conftest import csrf_from

TODAY = datetime.date.today()


def add(client, **fields):
    data = {"kind": "expense", "amount": "4.20", "category": "Coffee", "note": "",
            "date": TODAY.isoformat(), "then": "dashboard",
            "csrf_token": csrf_from(client.get("/add").text)}
    data.update(fields)
    return client.post("/transactions", data=data, follow_redirects=False)


def test_add_and_see_on_dashboard(client):
    r = add(client, note="<b>flat white</b>", amount="4.20", category="Coffee")
    assert r.status_code == 303 and r.headers["location"] == "/"
    page = client.get("/").text
    assert "−£4.20" in page
    notes = client.get("/transactions").text
    assert "&lt;b&gt;flat white&lt;/b&gt;" in notes   # escaped, not rendered as HTML
    assert "Spending by category" in page
    # Mockup layout: every tile is there; unbuilt ones say so instead of faking numbers.
    for tile in ["Net worth", "Cash", "Debt", "Budget: this week", "Bills:", "Savings goals",
                 "ISA allowance", "Debts", "Recent"]:
        assert f"<h2>{tile}" in page, tile
    assert page.count("Coming soon") == 9


def test_save_and_add_another(client):
    r = add(client, then="add")
    assert r.headers["location"] == "/add?saved=1"
    assert "Saved" in client.get("/add?saved=1").text


def test_unknown_redirect_target_goes_home(client):
    assert add(client, then="https://evil.example").headers["location"] == "/"


def test_bad_input_shows_errors(client):
    r = add(client, amount="-1", category="")
    assert r.status_code == 400 and "Please fix" in r.text


def test_missing_csrf_rejected(client):
    assert add(client, csrf_token="wrong").status_code == 403


def test_transactions_page_by_month_and_delete(client):
    add(client, amount="9.99", category="Books", date="2024-03-15")
    page = client.get("/transactions?month=2024-03").text
    assert "March 2024" in page and "−£9.99" in page
    tx_id = int(page.split('/transactions/')[1].split('/delete')[0])

    confirm = client.get(f"/transactions/{tx_id}/delete")
    assert "can't be undone" in confirm.text
    r = client.post(f"/transactions/{tx_id}/delete",
                    data={"csrf_token": csrf_from(confirm.text)}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/transactions?month=2024-03"
    assert "−£9.99" not in client.get("/transactions?month=2024-03").text
    assert client.get(f"/transactions/{tx_id}/delete").status_code == 404


def test_delete_needs_csrf(client):
    add(client, amount="1.23", category="Snacks", date="2024-04-01")
    page = client.get("/transactions?month=2024-04").text
    tx_id = int(page.split('/transactions/')[1].split('/delete')[0])
    r = client.post(f"/transactions/{tx_id}/delete", data={"csrf_token": "nope"})
    assert r.status_code == 403


def test_odd_month_param_falls_back(client):
    for bad in ["2026-13", "abcd", "1800-01", "2026-1", "'; DROP TABLE"]:
        assert client.get(f"/?month={bad}").status_code == 200


def test_oversized_body_rejected(client):
    r = client.post("/transactions", content=b"a" * 20_000,
                    headers={"content-type": "application/x-www-form-urlencoded"})
    assert r.status_code == 413


def test_headers_and_no_docs(anon):
    r = anon.get("/health")
    assert r.json() == {"status": "ok"}
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["cache-control"] == "no-store"
    assert anon.get("/docs").status_code == 404


def test_every_page_needs_login(anon):
    """Safety net: any route not on this list must bounce to /login."""
    public = {"/login", "/health"}
    checked = 0
    # Routes added straight to the app, plus those on the protected router
    # (FastAPI wraps an included router, so it isn't in app.routes directly).
    for route in [*app.routes, *protected.routes]:
        if not isinstance(route, APIRoute) or route.path in public:
            continue
        path = route.path.replace("{tx_id}", "1")
        for method in route.methods:
            r = anon.request(method, path, data={"csrf_token": "x"}, follow_redirects=False)
            assert r.status_code == 303 and r.headers["location"] == "/login", (method, path)
            checked += 1
    assert checked >= 7


def test_format_money():
    assert format_money(0) == "£0.00"
    assert format_money(123456) == "£1,234.56"
    assert format_money(-420) == "−£4.20"
    assert format_money(420, signed=True) == "+£4.20"
