"""Analytics over a set of normalized transactions.

All monetary math here is exact ``Decimal`` arithmetic, quantized to cents with
``ROUND_HALF_UP``. Conversion to JSON numbers happens at the API boundary, never
in this layer.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from src.domain import Transaction

_CENTS = Decimal("0.01")


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
