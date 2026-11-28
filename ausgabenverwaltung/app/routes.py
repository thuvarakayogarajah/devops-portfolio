from __future__ import annotations
import os 

from collections import defaultdict
from decimal import Decimal

from flask import Blueprint, current_app, jsonify, render_template, request

from app.models import (
    ValidationError,
    validate_amount,
    validate_category,
    validate_date,
    validate_month,
)

bp = Blueprint("main", __name__)


def _repo():
    return current_app.extensions["repository"]


def _config():
    return current_app.extensions["app_config"]


@bp.errorhandler(ValidationError)
def _handle_validation_error(exc: ValidationError):
    return jsonify(error=str(exc)), 400


@bp.get("/")
def index():
    return render_template("index.html", version=_config().version)


@bp.get("/health")
def health():
    """Liveness: is the process up? Must not touch the database.

    Kubernetes restarts the container when this fails, so a slow database
    must never be able to trigger a restart loop.
    """
    return jsonify(status="ok", version=_config().version)


@bp.get("/ready")
def ready():
    """Readiness: can this instance serve traffic? Checks the database."""
    if _repo().healthy():
        return jsonify(status="ready")
    return jsonify(status="unavailable"), 503


@bp.get("/api/expenses")
def list_expenses():
    month = request.args.get("month")
    expenses = _repo().list(validate_month(month) if month is not None else None)
    return jsonify([e.to_dict() for e in expenses])


@bp.post("/api/expenses")
def create_expense():
    payload = request.get_json(silent=True) or {}
    expense = _repo().add(
        amount=validate_amount(payload.get("amount")),
        category=validate_category(payload.get("category")),
        spent_on=validate_date(payload.get("date")),
    )
    return jsonify(expense.to_dict()), 201


@bp.get("/api/expenses/summary")
def expense_summary():
    """Totals per category for one month, e.g. ?month=2026-10."""
    month = validate_month(request.args.get("month"))
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for expense in _repo().list(month):
        totals[expense.category] += expense.amount
    return jsonify(
        month=month,
        total=str(sum(totals.values(), Decimal("0.00"))),
        by_category={category: str(amount) for category, amount in sorted(totals.items())},
    )


@bp.get("/api/expenses/<int:expense_id>")
def get_expense(expense_id: int):
    expense = _repo().get(expense_id)
    if expense is None:
        return jsonify(error="expense not found"), 404
    return jsonify(expense.to_dict())


@bp.delete("/api/expenses/<int:expense_id>")
def delete_expense(expense_id: int):
    if not _repo().delete(expense_id):
        return jsonify(error="expense not found"), 404
    return "", 204
