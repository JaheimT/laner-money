import re

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def form_token():
    page = client.get("/")
    return re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)


def test_add_and_list():
    token = form_token()
    r = client.post("/transactions", data={
        "kind": "expense", "amount": "4.20", "category": "Coffee",
        "note": "<b>flat white</b>", "date": "2026-11-22", "csrf_token": token,
    }, follow_redirects=False)
    assert r.status_code == 303
    page = client.get("/").text
    assert "−£4.20" in page
    assert "&lt;b&gt;flat white&lt;/b&gt;" in page   # escaped, not rendered as HTML


def test_bad_input_shows_errors():
    r = client.post("/transactions", data={
        "kind": "expense", "amount": "-1", "category": "", "note": "",
        "date": "2026-11-22", "csrf_token": form_token(),
    })
    assert r.status_code == 400 and "Please fix" in r.text


def test_missing_csrf_rejected():
    r = client.post("/transactions", data={
        "kind": "expense", "amount": "1", "category": "X", "date": "2026-11-22",
        "csrf_token": "wrong",
    })
    assert r.status_code == 403


def test_oversized_body_rejected():
    r = client.post("/transactions", content=b"a" * 20_000,
                    headers={"content-type": "application/x-www-form-urlencoded"})
    assert r.status_code == 413


def test_headers_and_no_docs():
    r = client.get("/health")
    assert r.json() == {"status": "ok"}
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert client.get("/docs").status_code == 404
