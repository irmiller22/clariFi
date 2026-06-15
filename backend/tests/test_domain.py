"""Tests for the canonical Transaction domain model."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.domain import Transaction


def _make(**overrides: object) -> Transaction:
    """Build a Transaction with sensible defaults, overriding as needed."""
    data: dict[str, object] = {
        "transaction_date": date(2025, 1, 5),
        "post_date": date(2025, 1, 6),
        "description": "SQ *CLEVER BARBER",
        "merchant": "SQ *CLEVER BARBER",
        "category": "Personal",
        "source_type": "Sale",
        "amount": Decimal("-45.74"),
        "memo": "",
    }
    data.update(overrides)
    return Transaction(**data)


class TestDerivedType:
    """`type` is derived from the amount sign."""

    def test_negative_amount_is_debit(self) -> None:
        assert _make(amount=Decimal("-10.00")).type == "debit"

    def test_positive_amount_is_credit(self) -> None:
        assert _make(amount=Decimal("100.00")).type == "credit"

    def test_zero_amount_is_credit(self) -> None:
        # Non-negative is treated as credit; zero is a degenerate edge case.
        assert _make(amount=Decimal("0.00")).type == "credit"


class TestDerivedMonth:
    """`month` is derived from the transaction date as a YYYY-MM key."""

    def test_month_key_is_zero_padded(self) -> None:
        assert _make(transaction_date=date(2025, 1, 5)).month == "2025-01"

    def test_month_key_double_digit_month(self) -> None:
        assert _make(transaction_date=date(2024, 12, 31)).month == "2024-12"


class TestMoneyExactness:
    """Money is an exact Decimal, never a float."""

    def test_amount_is_decimal_and_exact(self) -> None:
        tx = _make(amount=Decimal("-45.74"))
        assert isinstance(tx.amount, Decimal)
        assert tx.amount == Decimal("-45.74")


class TestImmutability:
    """The model is frozen — a normalized transaction is read-only."""

    def test_cannot_mutate_amount(self) -> None:
        tx = _make()
        with pytest.raises(ValidationError):
            tx.amount = Decimal("1.00")  # type: ignore[misc]


class TestSerialization:
    """Derived values are surfaced in the serialized output."""

    def test_dump_includes_derived_fields(self) -> None:
        dumped = _make(amount=Decimal("-45.74"), transaction_date=date(2025, 3, 1)).model_dump()
        assert dumped["type"] == "debit"
        assert dumped["month"] == "2025-03"
