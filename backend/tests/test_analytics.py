"""Unit tests for the analytics summary service."""

from datetime import date
from decimal import Decimal

from src.domain import Transaction
from src.services.analytics import (
    SpendingSummary,
    recurring_charges,
    spending_by_category,
    spending_timeline,
    summarize,
    top_merchants,
    trends,
)


def _tx(
    amount: str,
    category: str = "Misc",
    on: date = date(2025, 1, 1),
    merchant: str = "x",
) -> Transaction:
    return Transaction(
        transaction_date=on,
        post_date=on,
        description="x",
        merchant=merchant,
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


class TestSpendingTimeline:
    def test_empty_set_returns_empty_list(self) -> None:
        assert spending_timeline([]) == []

    def test_only_credits_returns_empty_list(self) -> None:
        assert spending_timeline([_tx("100.00", on=date(2025, 1, 1))]) == []

    def test_daily_buckets_with_cumulative(self) -> None:
        result = spending_timeline(
            [_tx("-10.00", on=date(2025, 1, 1)), _tx("-30.00", on=date(2025, 1, 3))],
            "day",
        )
        # Jan 2 has no spend but is gap-filled with 0; cumulative carries.
        assert [(p.date, p.amount, p.cumulative) for p in result] == [
            (date(2025, 1, 1), Decimal("10.00"), Decimal("10.00")),
            (date(2025, 1, 2), Decimal("0.00"), Decimal("10.00")),
            (date(2025, 1, 3), Decimal("30.00"), Decimal("40.00")),
        ]

    def test_same_day_amounts_sum(self) -> None:
        result = spending_timeline(
            [_tx("-10.00", on=date(2025, 1, 1)), _tx("-5.00", on=date(2025, 1, 1))], "day"
        )
        assert len(result) == 1
        assert result[0].amount == Decimal("15.00")

    def test_weekly_buckets_key_on_monday(self) -> None:
        # Jan 8 (Wed) and Jan 10 (Fri) 2025 both fall in the week of Mon Jan 6.
        result = spending_timeline(
            [_tx("-10.00", on=date(2025, 1, 8)), _tx("-20.00", on=date(2025, 1, 10))],
            "week",
        )
        assert len(result) == 1
        assert result[0].date == date(2025, 1, 6)
        assert result[0].amount == Decimal("30.00")

    def test_monthly_buckets_gap_fill_empty_months(self) -> None:
        result = spending_timeline(
            [_tx("-10.00", on=date(2025, 1, 15)), _tx("-30.00", on=date(2025, 3, 5))],
            "month",
        )
        # Feb has no spend but is filled; months keyed on the 1st.
        assert [(p.date, p.amount, p.cumulative) for p in result] == [
            (date(2025, 1, 1), Decimal("10.00"), Decimal("10.00")),
            (date(2025, 2, 1), Decimal("0.00"), Decimal("10.00")),
            (date(2025, 3, 1), Decimal("30.00"), Decimal("40.00")),
        ]

    def test_monthly_gap_fill_crosses_year_boundary(self) -> None:
        result = spending_timeline(
            [_tx("-10.00", on=date(2024, 12, 1)), _tx("-20.00", on=date(2025, 2, 1))],
            "month",
        )
        assert [p.date for p in result] == [
            date(2024, 12, 1),
            date(2025, 1, 1),
            date(2025, 2, 1),
        ]


class TestTrends:
    def test_empty_set_returns_empty_series(self) -> None:
        result = trends([])
        assert result.overall == []
        assert result.by_category == []

    def test_single_month_has_no_prior(self) -> None:
        result = trends([_tx("-100.00", on=date(2025, 1, 10))])
        assert len(result.overall) == 1
        point = result.overall[0]
        assert point.month == "2025-01"
        assert point.amount == Decimal("100.00")
        assert point.delta == Decimal("0.00")
        assert point.pct_change is None
        assert point.direction == "flat"

    def test_three_months_deltas_and_pct(self) -> None:
        result = trends(
            [
                _tx("-100.00", on=date(2025, 1, 1)),
                _tx("-150.00", on=date(2025, 2, 1)),
                _tx("-120.00", on=date(2025, 3, 1)),
            ]
        )
        overall = result.overall
        assert [p.month for p in overall] == ["2025-01", "2025-02", "2025-03"]
        # Feb: +50 on 100 -> +50%, up
        assert overall[1].delta == Decimal("50.00")
        assert overall[1].pct_change == Decimal("50.00")
        assert overall[1].direction == "up"
        # Mar: -30 on 150 -> -20%, down
        assert overall[2].delta == Decimal("-30.00")
        assert overall[2].pct_change == Decimal("-20.00")
        assert overall[2].direction == "down"

    def test_flat_month(self) -> None:
        result = trends([_tx("-50.00", on=date(2025, 1, 1)), _tx("-50.00", on=date(2025, 2, 1))])
        assert result.overall[1].delta == Decimal("0.00")
        assert result.overall[1].pct_change == Decimal("0.00")
        assert result.overall[1].direction == "flat"

    def test_zero_prior_month_guards_pct(self) -> None:
        # Jan spend, Feb none (gap-filled 0), Mar spend.
        result = trends([_tx("-100.00", on=date(2025, 1, 1)), _tx("-40.00", on=date(2025, 3, 1))])
        feb, mar = result.overall[1], result.overall[2]
        assert feb.amount == Decimal("0.00")
        assert feb.direction == "down"  # 100 -> 0
        assert mar.pct_change is None  # prior month was 0; can't divide
        assert mar.direction == "up"

    def test_dropped_category_drops_to_zero(self) -> None:
        result = trends(
            [
                _tx("-30.00", category="Gym", on=date(2025, 1, 1)),
                _tx("-30.00", category="Food", on=date(2025, 2, 1)),
            ]
        )
        gym = next(c for c in result.by_category if c.category == "Gym")
        assert gym.points[0].amount == Decimal("30.00")
        assert gym.points[1].amount == Decimal("0.00")
        assert gym.points[1].direction == "down"

    def test_new_category_rises_from_zero(self) -> None:
        result = trends(
            [
                _tx("-30.00", category="Food", on=date(2025, 1, 1)),
                _tx("-25.00", category="Travel", on=date(2025, 2, 1)),
            ]
        )
        travel = next(c for c in result.by_category if c.category == "Travel")
        assert travel.points[0].amount == Decimal("0.00")
        assert travel.points[1].amount == Decimal("25.00")
        assert travel.points[1].direction == "up"
        assert travel.points[1].pct_change is None  # rose from 0

    def test_lookback_window_keeps_true_delta(self) -> None:
        result = trends(
            [
                _tx("-100.00", on=date(2025, 1, 1)),
                _tx("-150.00", on=date(2025, 2, 1)),
                _tx("-120.00", on=date(2025, 3, 1)),
            ],
            months=2,
        )
        # Only Feb and Mar shown, but Feb keeps its delta vs Jan (not reset).
        assert [p.month for p in result.overall] == ["2025-02", "2025-03"]
        assert result.overall[0].delta == Decimal("50.00")
        assert result.overall[0].direction == "up"

    def test_category_filter_restricts_computation(self) -> None:
        result = trends(
            [
                _tx("-100.00", category="Food", on=date(2025, 1, 1)),
                _tx("-50.00", category="Gym", on=date(2025, 1, 1)),
            ],
            category="Food",
        )
        assert [c.category for c in result.by_category] == ["Food"]
        assert result.overall[0].amount == Decimal("100.00")


class TestTopMerchants:
    def test_empty_set_returns_empty_list(self) -> None:
        assert top_merchants([]) == []

    def test_only_credits_returns_empty_list(self) -> None:
        assert top_merchants([_tx("100.00", merchant="Payroll")]) == []

    def test_aggregates_and_ranks_by_spend(self) -> None:
        result = top_merchants(
            [
                _tx("-100.00", merchant="Amazon"),
                _tx("-20.00", merchant="Cafe"),
                _tx("-20.00", merchant="Cafe"),
                _tx("-20.00", merchant="Cafe"),
            ]
        )
        assert [(m.merchant, m.amount, m.count) for m in result] == [
            ("Amazon", Decimal("100.00"), 1),
            ("Cafe", Decimal("60.00"), 3),
        ]

    def test_rank_by_count(self) -> None:
        result = top_merchants(
            [
                _tx("-100.00", merchant="Amazon"),
                _tx("-20.00", merchant="Cafe"),
                _tx("-20.00", merchant="Cafe"),
                _tx("-20.00", merchant="Cafe"),
            ],
            by="count",
        )
        assert [m.merchant for m in result] == ["Cafe", "Amazon"]

    def test_limit_caps_results(self) -> None:
        result = top_merchants(
            [
                _tx("-90.00", merchant="A"),
                _tx("-50.00", merchant="B"),
                _tx("-10.00", merchant="C"),
            ],
            limit=2,
        )
        assert [m.merchant for m in result] == ["A", "B"]


def _monthly(merchant: str, amounts: list[str], start_month: int = 1) -> list[Transaction]:
    """Build one charge per month (on the 1st) for a merchant."""
    return [
        _tx(amt, merchant=merchant, on=date(2025, start_month + i, 1))
        for i, amt in enumerate(amounts)
    ]


class TestRecurringCharges:
    def test_empty_set_returns_empty_list(self) -> None:
        assert recurring_charges([]) == []

    def test_clean_monthly_subscription_detected(self) -> None:
        result = recurring_charges(_monthly("Netflix", ["-15.99", "-15.99", "-15.99"]))
        assert len(result) == 1
        charge = result[0]
        assert charge.merchant == "Netflix"
        assert charge.cadence == "monthly"
        assert charge.typical_amount == Decimal("15.99")
        assert charge.occurrences == 3
        assert charge.last_date == date(2025, 3, 1)
        assert charge.next_expected_date == date(2025, 4, 1)

    def test_weekly_subscription_detected(self) -> None:
        txns = [
            _tx("-10.00", merchant="Gym", on=date(2025, 1, 6)),
            _tx("-10.00", merchant="Gym", on=date(2025, 1, 13)),
            _tx("-10.00", merchant="Gym", on=date(2025, 1, 20)),
        ]
        result = recurring_charges(txns)
        assert len(result) == 1
        assert result[0].cadence == "weekly"
        assert result[0].next_expected_date == date(2025, 1, 27)

    def test_irregular_merchant_not_flagged(self) -> None:
        txns = [
            _tx("-10.00", merchant="Shop", on=date(2025, 1, 1)),
            _tx("-10.00", merchant="Shop", on=date(2025, 1, 5)),
            _tx("-10.00", merchant="Shop", on=date(2025, 3, 20)),
        ]
        assert recurring_charges(txns) == []

    def test_amount_drift_within_tolerance_detected(self) -> None:
        # ~3% spread on a ~10 mean stays under the 5% tolerance.
        result = recurring_charges(_monthly("Spotify", ["-10.00", "-10.20", "-9.90"]))
        assert len(result) == 1
        assert result[0].merchant == "Spotify"

    def test_amount_drift_outside_tolerance_not_flagged(self) -> None:
        assert recurring_charges(_monthly("Variable", ["-10.00", "-20.00", "-10.00"])) == []

    def test_too_few_occurrences_not_flagged(self) -> None:
        assert recurring_charges(_monthly("Twice", ["-9.99", "-9.99"])) == []

    def test_credits_ignored(self) -> None:
        txns = _monthly("Refunds", ["12.00", "12.00", "12.00"])  # positive -> credits
        assert recurring_charges(txns) == []
