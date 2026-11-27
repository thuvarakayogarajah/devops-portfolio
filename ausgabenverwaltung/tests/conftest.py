import pytest
from prometheus_client import CollectorRegistry

from app import create_app
from app.config import Config
from app.repository import InMemoryExpenseRepository


@pytest.fixture
def app():
    config = Config(database_url=None, version="test", log_level="WARNING")
    return create_app(
        config=config,
        repository=InMemoryExpenseRepository(),
        registry=CollectorRegistry(),
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def add_expense(client):
    def _add(amount="10.00", category="food", date="2026-10-15"):
        response = client.post(
            "/api/expenses", json={"amount": amount, "category": category, "date": date}
        )
        assert response.status_code == 201
        return response.get_json()

    return _add
