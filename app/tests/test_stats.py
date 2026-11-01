from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import routes
from app.routes.routes import Stats, bp


def make_expense(amount, category="food"):
    return SimpleNamespace(amount=amount, category=category)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(routes, "EXPENSES", [])
    app = FastAPI()
    app.include_router(bp)
    return TestClient(app)


def test_empty_stats():
    stats = Stats([])
    assert stats.count == 0
    assert stats.total == 0
    assert stats.by_category == {}


@pytest.mark.parametrize("amounts, expected_total", [
    ([12.5], 12.5),
    ([0.1, 0.2], 0.3),
    ([10, 20, 30.75], 60.75),
])
def test_total(amounts, expected_total):
    stats = Stats([make_expense(amount) for amount in amounts])
    assert stats.count == len(amounts)
    assert stats.total == expected_total


def test_by_category():
    expenses = [
        make_expense(10, "food"),
        make_expense(5.5, "food"),
        make_expense(80, "rent"),
    ]
    assert Stats(expenses).by_category == {"food": 15.5, "rent": 80}


def test_add_and_list_expenses(client):
    expense = {"description": "Groceries", "amount": 42.9, "category": "food", "date": "2026-10-30"}

    response = client.post("/api/v1/expenses", json=expense)
    assert response.status_code == 201
    assert response.json() == expense

    assert client.get("/api/v1/expenses").json() == [expense]


def test_rejects_non_positive_amount(client):
    expense = {"description": "Refund", "amount": 0, "category": "food", "date": "2026-10-30"}

    response = client.post("/api/v1/expenses", json=expense)

    assert response.status_code == 422
    assert client.get("/api/v1/expenses").json() == []


def test_stats_endpoint(client):
    client.post("/api/v1/expenses", json={"description": "Lunch", "amount": 15, "category": "food", "date": "2026-10-30"})
    client.post("/api/v1/expenses", json={"description": "Train", "amount": 8.4, "category": "transport", "date": "2026-10-30"})

    response = client.get("/api/v1/expenses/stats")

    assert response.status_code == 200
    assert response.json() == {"count": 2, "total": 23.4, "by_category": {"food": 15, "transport": 8.4}}


def test_health():
    response = TestClient(routes.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
