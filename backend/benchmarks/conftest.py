"""Shared fixtures for the performance benchmark suite.

Builds a deterministic ~10k-transaction dataset (no randomness, so timings are
comparable run-to-run) in the three shapes the hot paths consume: raw CSV text,
parsed ``TransactionCreate`` rows, and normalized ``Transaction`` objects.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.domain import Transaction
from src.schemas import TransactionCreate

N = 10_000

_CATEGORIES = [
    "Groceries",
    "Dining",
    "Transport",
    "Shopping",
    "Utilities",
    "Health",
    "Travel",
    "Entertainment",
    "Income",
    "Fees",
]
_MERCHANTS = [f"MERCHANT {i:02d}" for i in range(50)]
_BASE = date(2025, 1, 1)


def _amount(i: int) -> Decimal:
    """Mostly debits; every 10th row is a positive credit."""
    magnitude = Decimal(i % 300) + Decimal("1.99")
    return magnitude if i % 10 == 0 else -magnitude


def _day(i: int) -> date:
    return _BASE + timedelta(days=i % 365)


@pytest.fixture(scope="session")
def transactions() -> list[Transaction]:
    return [
        Transaction(
            transaction_date=_day(i),
            post_date=_day(i),
            description=_MERCHANTS[i % len(_MERCHANTS)],
            merchant=_MERCHANTS[i % len(_MERCHANTS)],
            category=_CATEGORIES[i % len(_CATEGORIES)],
            source_type="Payment" if i % 10 == 0 else "Sale",
            amount=_amount(i),
        )
        for i in range(N)
    ]


@pytest.fixture(scope="session")
def rows() -> list[TransactionCreate]:
    out: list[TransactionCreate] = []
    for i in range(N):
        d = _day(i)
        stamp = f"{d.month:02d}/{d.day:02d}/{d.year:04d}"
        out.append(
            TransactionCreate(
                transaction_date=stamp,
                post_date=stamp,
                description=_MERCHANTS[i % len(_MERCHANTS)],
                category=_CATEGORIES[i % len(_CATEGORIES)],
                type="Payment" if i % 10 == 0 else "Sale",
                amount=_amount(i),
                memo="",
            )
        )
    return out


@pytest.fixture(scope="session")
def csv_text(rows: list[TransactionCreate]) -> str:
    header = "Transaction Date,Post Date,Description,Category,Type,Amount,Memo"
    lines = [header]
    lines.extend(
        f"{r.transaction_date},{r.post_date},{r.description},{r.category},{r.type},{r.amount},"
        for r in rows
    )
    return "\n".join(lines) + "\n"
