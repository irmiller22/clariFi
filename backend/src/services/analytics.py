"""Analytics over a set of normalized transactions.

All monetary math here is exact ``Decimal`` arithmetic, quantized to cents with
``ROUND_HALF_UP``. Conversion to JSON numbers happens at the API boundary, never
in this layer.
"""

from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from src.domain import Transaction

_CENTS = Decimal("0.01")
_HUNDRED = Decimal(100)


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
