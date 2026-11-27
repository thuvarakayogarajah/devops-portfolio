import pytest


def test_list_is_empty_initially(client):
    response = client.get("/api/expenses")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_expense(client):
    response = client.post(
        "/api/expenses", json={"amount": "12.5", "category": " Food ", "date": "2026-10-30"}
    )
    assert response.status_code == 201
    assert response.get_json() == {
        "id": 1,
        "amount": "12.50",
        "category": "food",
        "date": "2026-10-30",
    }


def test_create_expense_accepts_numeric_amount(client):
    response = client.post(
        "/api/expenses", json={"amount": 7, "category": "transport", "date": "2026-10-01"}
    )
    assert response.status_code == 201
    assert response.get_json()["amount"] == "7.00"


@pytest.mark.parametrize(
    "payload",
    [
        {"amount": "0", "category": "food", "date": "2026-10-01"},
        {"amount": "-5", "category": "food", "date": "2026-10-01"},
        {"amount": "1.234", "category": "food", "date": "2026-10-01"},
        {"amount": "abc", "category": "food", "date": "2026-10-01"},
        {"amount": "NaN", "category": "food", "date": "2026-10-01"},
        {"amount": "1000000", "category": "food", "date": "2026-10-01"},
        {"amount": True, "category": "food", "date": "2026-10-01"},
        {"amount": "5", "category": "cars", "date": "2026-10-01"},
        {"amount": "5", "category": "food", "date": "2026-13-01"},
        {"amount": "5", "category": "food", "date": 20261001},
        {},
    ],
)
def test_create_expense_rejects_invalid_input(client, payload):
    response = client.post("/api/expenses", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_list_filters_by_month(client, add_expense):
    add_expense(date="2026-09-30")
    october = add_expense(date="2026-10-01")

    response = client.get("/api/expenses?month=2026-10")
    assert response.get_json() == [october]


def test_list_rejects_invalid_month(client):
    assert client.get("/api/expenses?month=2026-1").status_code == 400


def test_get_and_delete_expense(client, add_expense):
    expense = add_expense()

    assert client.get(f"/api/expenses/{expense['id']}").get_json() == expense
    assert client.delete(f"/api/expenses/{expense['id']}").status_code == 204
    assert client.get(f"/api/expenses/{expense['id']}").status_code == 404


def test_delete_unknown_expense_returns_404(client):
    assert client.delete("/api/expenses/99").status_code == 404
