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
# Leading payment-processor prefix, e.g. "SQ *", "TST*", "PYPL *".
_PROCESSOR_PREFIX_RE = re.compile(r"^\S{1,6}\s*\*\s*")
# A trailing store-number / reference token, e.g. "#1234" or a bare digit run.
_TRAILING_NUMBER_RE = re.compile(r"^#?\d{2,}$")


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
    """Canonicalize a merchant name so the same merchant aggregates together.

    Heuristics (applied to the whitespace-collapsed description):
    - strip a leading payment-processor prefix (``SQ *``, ``TST*``, ``PYPL *``);
    - strip trailing store-number / reference tokens (``#1234`` or bare digit
      runs like a pump or terminal id).

    This intentionally does not attempt city/state stripping — that's ambiguous
    and risks mangling real names; store numbers and processor prefixes cover the
    common "same merchant, different suffix" cases. Falls back to the collapsed
    description if stripping would leave nothing.
    """
    text = _PROCESSOR_PREFIX_RE.sub("", _collapse_whitespace(description))
    tokens = text.split()
    while len(tokens) > 1 and _TRAILING_NUMBER_RE.match(tokens[-1]):
        tokens.pop()
    return " ".join(tokens) or _collapse_whitespace(description)


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
