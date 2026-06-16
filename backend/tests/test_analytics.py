"""Unit tests for the analytics summary service."""

from datetime import date
from decimal import Decimal

from src.domain import Transaction
from src.services.analytics import (
    SpendingSummary,
    spending_by_category,
    summarize,
)


def _tx(amount: str, category: str = "Misc") -> Transaction:
    return Transaction(
        transaction_date=date(2025, 1, 1),
        post_date=date(2025, 1, 1),
        description="x",
        merchant="x",
        category=category,
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


class TestSpendingByCategory:
    def test_empty_set_returns_empty_list(self) -> None:
        assert spending_by_category([]) == []

    def test_only_credits_returns_empty_list(self) -> None:
        # No outflows -> nothing to break down.
        assert spending_by_category([_tx("2000.00", category="Income")]) == []

    def test_groups_and_counts_by_category(self) -> None:
        result = spending_by_category(
            [
                _tx("-60.00", category="Groceries"),
                _tx("-40.00", category="Groceries"),
                _tx("-100.00", category="Rent"),
            ]
        )
        by_cat = {c.category: c for c in result}
        assert by_cat["Groceries"].amount == Decimal("100.00")
        assert by_cat["Groceries"].count == 2
        assert by_cat["Rent"].amount == Decimal("100.00")
        assert by_cat["Rent"].count == 1

    def test_sorted_by_amount_descending(self) -> None:
        result = spending_by_category(
            [
                _tx("-10.00", category="Small"),
                _tx("-90.00", category="Big"),
                _tx("-50.00", category="Mid"),
            ]
        )
        assert [c.category for c in result] == ["Big", "Mid", "Small"]

    def test_percentages_are_share_of_total_spend(self) -> None:
        result = spending_by_category([_tx("-60.00", category="A"), _tx("-40.00", category="B")])
        by_cat = {c.category: c.percentage for c in result}
        assert by_cat["A"] == Decimal("60.00")
        assert by_cat["B"] == Decimal("40.00")
        assert sum(c.percentage for c in result) == Decimal("100.00")

    def test_credits_excluded_from_category_spend(self) -> None:
        # A refund (positive) in Groceries must not reduce or inflate the
        # outflow total for that category.
        result = spending_by_category(
            [_tx("-50.00", category="Groceries"), _tx("20.00", category="Groceries")]
        )
        assert len(result) == 1
        assert result[0].amount == Decimal("50.00")
        assert result[0].count == 1

    def test_uncategorized_groups_like_any_other(self) -> None:
        result = spending_by_category(
            [_tx("-30.00", category="Uncategorized"), _tx("-10.00", category="Uncategorized")]
        )
        assert len(result) == 1
        assert result[0].category == "Uncategorized"
        assert result[0].amount == Decimal("40.00")
