def test_summary_for_empty_month(client):
    response = client.get("/api/expenses/summary?month=2026-10")
    assert response.status_code == 200
    assert response.get_json() == {"month": "2026-10", "total": "0.00", "by_category": {}}


def test_summary_sums_per_category(client, add_expense):
    add_expense(amount="0.10", category="food")
    add_expense(amount="0.20", category="food")
    add_expense(amount="850", category="housing")

    body = client.get("/api/expenses/summary?month=2026-10").get_json()
    # 0.1 + 0.2 is exactly 0.30 with Decimal, not 0.30000000000000004.
    assert body == {
        "month": "2026-10",
        "total": "850.30",
        "by_category": {"food": "0.30", "housing": "850.00"},
    }


def test_summary_ignores_other_months(client, add_expense):
    add_expense(amount="5", date="2026-09-30")
    add_expense(amount="7", date="2026-10-01")

    body = client.get("/api/expenses/summary?month=2026-10").get_json()
    assert body["total"] == "7.00"


def test_summary_requires_month(client):
    assert client.get("/api/expenses/summary").status_code == 400
