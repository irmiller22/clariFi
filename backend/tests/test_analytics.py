"""Unit tests for the analytics summary service."""

from datetime import date
from decimal import Decimal

from src.domain import Transaction
from src.services.analytics import SpendingSummary, summarize


def _tx(amount: str) -> Transaction:
    return Transaction(
        transaction_date=date(2025, 1, 1),
        post_date=date(2025, 1, 1),
        description="x",
        merchant="x",
        category="Misc",
        source_type="Sale",
        amount=Decimal(amount),
    )


class TestSummarize:
    def test_empty_set_is_all_zero_without_dividing_by_zero(self) -> None:
        result = summarize([])
        assert result == SpendingSummary(
            total_spent=Decimal("0.00"),
            total_income=Decimal("0.00"),
            net_amount=Decimal("0.00"),
            transaction_count=0,
            avg_transaction_amount=Decimal("0.00"),
        )

    def test_mixed_debits_and_credits(self) -> None:
        result = summarize([_tx("-50.00"), _tx("-40.00"), _tx("2000.00")])
        assert result.total_spent == Decimal("90.00")
        assert result.total_income == Decimal("2000.00")
        assert result.net_amount == Decimal("1910.00")
        assert result.transaction_count == 3

    def test_average_is_mean_magnitude(self) -> None:
        # (50 + 40 + 2000) / 3 = 696.666... -> 696.67 (round half up)
        result = summarize([_tx("-50.00"), _tx("-40.00"), _tx("2000.00")])
        assert result.avg_transaction_amount == Decimal("696.67")

    def test_money_is_decimal_quantized_to_cents(self) -> None:
        result = summarize([_tx("-10.005")])
        # 10.005 rounds half up to 10.01.
        assert isinstance(result.total_spent, Decimal)
        assert result.total_spent == Decimal("10.01")

    def test_only_debits(self) -> None:
        result = summarize([_tx("-12.50"), _tx("-7.50")])
        assert result.total_spent == Decimal("20.00")
        assert result.total_income == Decimal("0.00")
        assert result.net_amount == Decimal("-20.00")
