"""Analytics over a set of normalized transactions.

All monetary math here is exact ``Decimal`` arithmetic, quantized to cents with
``ROUND_HALF_UP``. Conversion to JSON numbers happens at the API boundary, never
in this layer.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from src.domain import Transaction

_CENTS = Decimal("0.01")
_HUNDRED = Decimal(100)

Granularity = Literal["day", "week", "month"]
Direction = Literal["up", "down", "flat"]
RankBy = Literal["spend", "count"]


def _to_cents(value: Decimal) -> Decimal:
    """Quantize a monetary value to cents using round-half-up."""
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class SpendingSummary:
    """Aggregate spending metrics (all money as exact, cent-quantized Decimal).

    - ``total_spent`` — sum of outflows (debits), as a positive amount.
    - ``total_income`` — sum of inflows (credits).
    - ``net_amount`` — ``total_income - total_spent``.
    - ``avg_transaction_amount`` — mean transaction magnitude
      (``(total_spent + total_income) / count``), 0 when there are none.
    """

    total_spent: Decimal
    total_income: Decimal
    net_amount: Decimal
    transaction_count: int
    avg_transaction_amount: Decimal


def summarize(transactions: list[Transaction]) -> SpendingSummary:
    """Compute aggregate spending metrics for a set of transactions."""
    spent = -sum((t.amount for t in transactions if t.amount < 0), Decimal(0))
    income = sum((t.amount for t in transactions if t.amount > 0), Decimal(0))
    count = len(transactions)
    avg = (spent + income) / count if count else Decimal(0)

    return SpendingSummary(
        total_spent=_to_cents(spent),
        total_income=_to_cents(income),
        net_amount=_to_cents(income - spent),
        transaction_count=count,
        avg_transaction_amount=_to_cents(avg),
    )


@dataclass(frozen=True)
class CategorySpending:
    """Spend for a single category (a slice of the spending breakdown).

    ``amount`` is the total *outflow* for the category (positive), ``count`` the
    number of spend transactions, and ``percentage`` the category's share of
    total spend (0-100). This is a spend breakdown, so credits/inflows
    (income, refunds) are not counted.
    """

    category: str
    amount: Decimal
    count: int
    percentage: Decimal


def spending_by_category(transactions: list[Transaction]) -> list[CategorySpending]:
    """Aggregate outflows per category, sorted by spend descending.

    Returns an empty list when there is no spend (e.g. no transactions, or only
    credits).
    """
    debits = [t for t in transactions if t.amount < 0]
    total = -sum((t.amount for t in debits), Decimal(0))
    if total <= 0:
        return []

    sums: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    counts: dict[str, int] = defaultdict(int)
    for t in debits:
        sums[t.category] += -t.amount
        counts[t.category] += 1

    breakdown = [
        CategorySpending(
            category=category,
            amount=_to_cents(amount),
            count=counts[category],
            percentage=(amount / total * _HUNDRED).quantize(_CENTS, rounding=ROUND_HALF_UP),
        )
        for category, amount in sums.items()
    ]
    breakdown.sort(key=lambda c: c.amount, reverse=True)
    return breakdown


@dataclass(frozen=True)
class TimelinePoint:
    """Spend in a single time bucket, with the running cumulative total.

    ``date`` is the bucket's start (the day itself, the Monday of the week, or
    the first of the month). ``amount`` is the bucket's outflow (positive);
    ``cumulative`` is the running sum of spend through this bucket.
    """

    date: date
    amount: Decimal
    cumulative: Decimal


def _bucket_start(day: date, granularity: Granularity) -> date:
    """Return the canonical start date of the bucket ``day`` falls in."""
    if granularity == "day":
        return day
    if granularity == "week":
        return day - timedelta(days=day.weekday())  # Monday
    return day.replace(day=1)


def _next_bucket(start: date, granularity: Granularity) -> date:
    """Return the start of the bucket immediately following ``start``."""
    if granularity == "day":
        return start + timedelta(days=1)
    if granularity == "week":
        return start + timedelta(weeks=1)
    if start.month == 12:
        return start.replace(year=start.year + 1, month=1)
    return start.replace(month=start.month + 1)


def spending_timeline(
    transactions: list[Transaction], granularity: Granularity = "month"
) -> list[TimelinePoint]:
    """Bucket outflows over time, gap-filling empty interior periods.

    Buckets run from the first to the last period that has spend; periods in
    between with no spend are emitted with amount 0 (cumulative stays flat), so
    a line chart is continuous. Credits are excluded; no-spend input returns [].
    """
    buckets: dict[date, Decimal] = defaultdict(lambda: Decimal(0))
    for t in transactions:
        if t.amount < 0:
            buckets[_bucket_start(t.transaction_date, granularity)] += -t.amount
    if not buckets:
        return []

    points: list[TimelinePoint] = []
    cumulative = Decimal(0)
    current, end = min(buckets), max(buckets)
    while current <= end:
        amount = buckets.get(current, Decimal(0))
        cumulative += amount
        points.append(TimelinePoint(current, _to_cents(amount), _to_cents(cumulative)))
        current = _next_bucket(current, granularity)
    return points


@dataclass(frozen=True)
class MonthlyPoint:
    """One month in a spend series, with change vs the previous month.

    ``delta`` is ``amount - previous month's amount``; ``pct_change`` is the
    percentage change, or ``None`` when there is no comparable prior month
    (the first month, or a prior month with zero spend — the zero-base guard).
    """

    month: str  # YYYY-MM
    amount: Decimal
    delta: Decimal
    pct_change: Decimal | None
    direction: Direction


@dataclass(frozen=True)
class CategoryTrend:
    """A per-category monthly spend series."""

    category: str
    points: list[MonthlyPoint]


@dataclass(frozen=True)
class SpendingTrends:
    """Month-over-month spend trends, overall and broken down by category."""

    overall: list[MonthlyPoint]
    by_category: list[CategoryTrend]


def _month_range(start: str, end: str) -> list[str]:
    """Inclusive list of YYYY-MM keys from ``start`` to ``end`` (gap-filled)."""
    start_year, start_month = (int(part) for part in start.split("-"))
    end_year, end_month = (int(part) for part in end.split("-"))
    keys: list[str] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        keys.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return keys


def _direction(delta: Decimal) -> Direction:
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "flat"


def _monthly_series(month_keys: list[str], amounts: dict[str, Decimal]) -> list[MonthlyPoint]:
    """Build a MonthlyPoint series over ``month_keys`` from monthly ``amounts``."""
    points: list[MonthlyPoint] = []
    prev: Decimal | None = None
    for month in month_keys:
        amount = _to_cents(amounts.get(month, Decimal(0)))
        if prev is None:
            point = MonthlyPoint(month, amount, Decimal("0.00"), None, "flat")
        else:
            delta = amount - prev
            pct = None
            if prev > 0:
                pct = (delta / prev * _HUNDRED).quantize(_CENTS, rounding=ROUND_HALF_UP)
            point = MonthlyPoint(month, amount, delta, pct, _direction(delta))
        points.append(point)
        prev = amount
    return points


def trends(
    transactions: list[Transaction],
    *,
    category: str | None = None,
    months: int | None = None,
) -> SpendingTrends:
    """Compute month-over-month spend trends, overall and per category.

    Months are gap-filled across the full range, so a category that disappears
    shows a drop to 0 and a new category rises from 0. ``category`` restricts the
    whole computation to one category; ``months`` keeps only the most recent N
    months (applied after deltas, so the window's first month keeps its true
    delta). Credits are excluded; no-spend input returns empty series.
    """
    debits = [
        t for t in transactions if t.amount < 0 and (category is None or t.category == category)
    ]
    if not debits:
        return SpendingTrends(overall=[], by_category=[])

    overall_amounts: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    per_category: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: defaultdict(lambda: Decimal(0))
    )
    for t in debits:
        overall_amounts[t.month] += -t.amount
        per_category[t.category][t.month] += -t.amount

    month_keys = _month_range(min(overall_amounts), max(overall_amounts))

    def window(points: list[MonthlyPoint]) -> list[MonthlyPoint]:
        return points[-months:] if months is not None else points

    overall = window(_monthly_series(month_keys, overall_amounts))
    by_category = [
        CategoryTrend(category=cat, points=window(_monthly_series(month_keys, amounts)))
        for cat, amounts in sorted(per_category.items())
    ]
    return SpendingTrends(overall=overall, by_category=by_category)


@dataclass(frozen=True)
class MerchantSpending:
    """Total spend at a single (canonicalized) merchant."""

    merchant: str
    amount: Decimal
    count: int


def top_merchants(
    transactions: list[Transaction],
    *,
    limit: int = 10,
    by: RankBy = "spend",
) -> list[MerchantSpending]:
    """Rank merchants by total spend (default) or transaction frequency.

    Groups outflows by the canonicalized ``merchant`` (see the normalizer), so
    the same merchant with different store-number suffixes aggregates together.
    Ties break on the other metric. Credits are excluded; returns at most
    ``limit`` entries, and [] when there is no spend.
    """
    sums: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    counts: dict[str, int] = defaultdict(int)
    for t in transactions:
        if t.amount < 0:
            sums[t.merchant] += -t.amount
            counts[t.merchant] += 1
    if not sums:
        return []

    merchants = [
        MerchantSpending(merchant=merchant, amount=_to_cents(amount), count=counts[merchant])
        for merchant, amount in sums.items()
    ]
    if by == "count":
        merchants.sort(key=lambda m: (m.count, m.amount), reverse=True)
    else:
        merchants.sort(key=lambda m: (m.amount, m.count), reverse=True)
    return merchants[:limit]
