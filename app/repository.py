from __future__ import annotations

import logging
import threading
from datetime import date
from decimal import Decimal
from typing import Protocol

from app.config import Config
from app.models import Expense

log = logging.getLogger(__name__)


class ExpenseRepository(Protocol):
    """Storage contract. Routes depend on this, never on a concrete backend."""

    def list(self, month: str | None = None) -> list[Expense]: ...
    def get(self, expense_id: int) -> Expense | None: ...
    def add(self, amount: Decimal, category: str, spent_on: date) -> Expense: ...
    def delete(self, expense_id: int) -> bool: ...
    def healthy(self) -> bool: ...


def _in_month(expense: Expense, month: str | None) -> bool:
    return month is None or expense.spent_on.isoformat().startswith(month)


class InMemoryExpenseRepository:
    """Default backend. Data is lost when the process exits."""

    def __init__(self) -> None:
        self._expenses: dict[int, Expense] = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def list(self, month: str | None = None) -> list[Expense]:
        with self._lock:
            return sorted(
                (e for e in self._expenses.values() if _in_month(e, month)),
                key=lambda e: (e.spent_on, e.id),
            )

    def get(self, expense_id: int) -> Expense | None:
        with self._lock:
            return self._expenses.get(expense_id)

    def add(self, amount: Decimal, category: str, spent_on: date) -> Expense:
        with self._lock:
            expense = Expense(id=self._next_id, amount=amount, category=category, spent_on=spent_on)
            self._expenses[expense.id] = expense
            self._next_id += 1
            return expense

    def delete(self, expense_id: int) -> bool:
        with self._lock:
            return self._expenses.pop(expense_id, None) is not None

    def healthy(self) -> bool:
        return True


class PostgresExpenseRepository:
    """Postgres backend, used via Docker Compose and in production."""

    _COLUMNS = "id, amount, category, spent_on"

    def __init__(self, dsn: str) -> None:
        from psycopg_pool import ConnectionPool

        self._pool = ConnectionPool(dsn, min_size=1, max_size=5, open=True)
        self._create_schema()

    def _create_schema(self) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id       SERIAL PRIMARY KEY,
                    amount   NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
                    category TEXT NOT NULL,
                    spent_on DATE NOT NULL
                )
                """
            )

    def list(self, month: str | None = None) -> list[Expense]:
        query = f"SELECT {self._COLUMNS} FROM expenses"
        params: tuple = ()
        if month is not None:
            query += " WHERE to_char(spent_on, 'YYYY-MM') = %s"
            params = (month,)
        query += " ORDER BY spent_on, id"
        with self._pool.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Expense(*row) for row in rows]

    def get(self, expense_id: int) -> Expense | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                f"SELECT {self._COLUMNS} FROM expenses WHERE id = %s", (expense_id,)
            ).fetchone()
        return Expense(*row) if row else None

    def add(self, amount: Decimal, category: str, spent_on: date) -> Expense:
        with self._pool.connection() as conn:
            row = conn.execute(
                "INSERT INTO expenses (amount, category, spent_on) VALUES (%s, %s, %s) "
                f"RETURNING {self._COLUMNS}",
                (amount, category, spent_on),
            ).fetchone()
        return Expense(*row)

    def delete(self, expense_id: int) -> bool:
        with self._pool.connection() as conn:
            result = conn.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        return result.rowcount > 0

    def healthy(self) -> bool:
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            log.exception("database health check failed")
            return False


def create_repository(config: Config) -> ExpenseRepository:
    if config.database_url:
        log.info("using postgres repository")
        return PostgresExpenseRepository(config.database_url)
    # In-memory state is per gunicorn worker and lost on restart. Fine for tests
    # and local development; set DATABASE_URL for anything else.
    log.warning(
        "no DATABASE_URL set, using in-memory repository: "
        "state is per-process and is lost on restart"
    )
    return InMemoryExpenseRepository()
