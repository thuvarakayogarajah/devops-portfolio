from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass
class Expense:
    id: int
    amount: Decimal
    category: str
    spent_on: date

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "amount": str(self.amount),
            "category": self.category,
            "date": self.spent_on.isoformat(),
        }


class ValidationError(ValueError):
    """Raised when client input does not satisfy the Expense invariants."""


CATEGORIES = ("foodx", "housing", "transport", "leisure", "other")
MAX_AMOUNT = Decimal("1000000")
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def validate_amount(raw: Any) -> Decimal:
    # bool is a subclass of int, so `true` would otherwise become 1.00.
    if isinstance(raw, bool) or not isinstance(raw, str | int | float):
        raise ValidationError("amount must be a number or a numeric string")
    try:
        amount = Decimal(str(raw))
    except InvalidOperation:
        raise ValidationError("amount must be a number") from None
    if not amount.is_finite() or amount <= 0:
        raise ValidationError("amount must be greater than 0")
    if amount >= MAX_AMOUNT:
        raise ValidationError(f"amount must be less than {MAX_AMOUNT}")
    if amount.as_tuple().exponent < -2:
        raise ValidationError("amount must have at most 2 decimal places")
    return amount.quantize(Decimal("0.01"))


def validate_category(raw: Any) -> str:
    if not isinstance(raw, str) or raw.strip().lower() not in CATEGORIES:
        raise ValidationError(f"category must be one of: {', '.join(CATEGORIES)}")
    return raw.strip().lower()


def validate_date(raw: Any) -> date:
    if not isinstance(raw, str):
        raise ValidationError("date must be a string in the format YYYY-MM-DD")
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise ValidationError("date must be a valid date in the format YYYY-MM-DD") from None


def validate_month(raw: Any) -> str:
    if not isinstance(raw, str) or not MONTH_PATTERN.match(raw):
        raise ValidationError("month must be in the format YYYY-MM")
    return raw
