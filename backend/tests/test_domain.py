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


class TestKind:
    """`kind` classifies each transaction for analytics."""

    def test_credit_card_payment_by_source_type(self) -> None:
        # A credit-card "Payment" (paying your card) is internal money movement.
        assert _make(source_type="Payment", amount=Decimal("500.00")).kind == "card_payment"

    def test_card_payment_by_description(self) -> None:
        tx = _make(description="Payment to Chase card 4796", amount=Decimal("-300.00"))
        assert tx.kind == "card_payment"

    def test_transfer_by_description(self) -> None:
        tx = _make(description="Online Transfer to SAV ...5168", amount=Decimal("-500.00"))
        assert tx.kind == "transfer"

    def test_fee(self) -> None:
        assert _make(description="MONTHLY SERVICE FEE", amount=Decimal("-12.00")).kind == "fee"

    def test_spending_default(self) -> None:
        assert _make(source_type="Sale", amount=Decimal("-20.00")).kind == "spending"

    def test_income_default(self) -> None:
        # A positive that isn't a payment/transfer (e.g. a refund) is income.
        assert _make(source_type="Return", amount=Decimal("30.00")).kind == "income"

    def test_is_money_movement(self) -> None:
        assert _make(source_type="Payment", amount=Decimal(100)).is_money_movement is True
        assert _make(description="Transfer of funds", amount=Decimal(-100)).is_money_movement
        assert _make(source_type="Sale", amount=Decimal(-10)).is_money_movement is False
        assert (
            _make(description="MONTHLY SERVICE FEE", amount=Decimal(-5)).is_money_movement is False
        )
