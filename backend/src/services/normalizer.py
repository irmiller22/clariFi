"""Normalize validated CSV rows into canonical Transaction domain objects.

This is the single place where the loose, string-shaped ``TransactionCreate``
(straight off the CSV) becomes a strongly-typed :class:`~src.domain.Transaction`
with a real ``date`` and an exact ``Decimal`` amount. See ``src.domain`` for the
amount-sign convention.
"""

import re
from datetime import date

from src.domain import Transaction
from src.schemas import TransactionCreate

_WHITESPACE_RE = re.compile(r"\s+")


def _parse_date(value: str) -> date:
    """Parse an ``MM/DD/YYYY`` string into a real :class:`datetime.date`.

    Raises ``ValueError`` for anything that isn't a valid calendar date. The
    schema only checks the *format* leniently (it accepts e.g. ``02/31``), so
    this is where calendar-invalid dates are actually rejected.
    """
    parts = value.strip().split("/")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Invalid date, expected MM/DD/YYYY: {value!r}")
    month, day, year = (int(part) for part in parts)
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise ValueError(f"Invalid date, expected MM/DD/YYYY: {value!r}") from exc


def _collapse_whitespace(text: str) -> str:
    """Trim and collapse runs of internal whitespace to single spaces."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def _normalize_merchant(description: str) -> str:
    """Lightly normalize a merchant string from the description.

    For now this is just whitespace normalization. Deeper canonicalization
    (stripping store numbers, city/state suffixes, so the same merchant
    aggregates together) is handled by the top-merchants analytics (LAT-78).
    """
    return _collapse_whitespace(description)


def normalize(row: TransactionCreate) -> Transaction:
    """Convert one validated CSV row into a canonical :class:`Transaction`."""
    description = _collapse_whitespace(row.description)
    return Transaction(
        transaction_date=_parse_date(row.transaction_date),
        post_date=_parse_date(row.post_date),
        description=description,
        merchant=_normalize_merchant(description),
        category=row.category,
        source_type=row.type,
        amount=row.amount,
        memo=row.memo or "",
    )


def normalize_many(rows: list[TransactionCreate]) -> list[Transaction]:
    """Normalize a list of rows, preserving order."""
    return [normalize(row) for row in rows]
