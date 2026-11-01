from dataclasses import dataclass
from datetime import date

from fastapi import FastAPI, APIRouter
from pydantic import BaseModel, Field

app = FastAPI()
bp = APIRouter(prefix="/api/v1", tags=["expenses"])


class Expense(BaseModel):
    description: str
    amount: float = Field(gt=0)
    category: str
    date: date


@dataclass
class Stats:
    expenses: list

    @property
    def count(self):
        return len(self.expenses)

    @property
    def total(self):
        return round(sum(expense.amount for expense in self.expenses), 2)

    @property
    def by_category(self):
        totals = {}
        for expense in self.expenses:
            totals[expense.category] = round(totals.get(expense.category, 0) + expense.amount, 2)
        return totals


EXPENSES = []  # placeholder until a repository exists


@bp.get("/expenses")
def list_expenses():
    return EXPENSES


@bp.post("/expenses", status_code=201)
def add_expense(expense: Expense):
    EXPENSES.append(expense)
    return expense


@bp.get("/expenses/stats")
def get_stats():
    stats = Stats(EXPENSES)
    return {"count": stats.count, "total": stats.total, "by_category": stats.by_category}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# include after all routes are defined, otherwise they are not registered
app.include_router(bp)
