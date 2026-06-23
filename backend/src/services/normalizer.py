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
# A trailing store-number / reference token: "#1234", a bare digit run, or a
# short alphanumeric ref like "F1234" / "12345A".
_TRAILING_REF_RE = re.compile(r"^(#\d+|\d{2,}|[A-Z]{1,3}\d{3,}|\d{3,}[A-Z]{1,3})$")
# US state (and DC) postal codes, used to anchor "CITY ST" location stripping.
_US_STATES = frozenset(
    [
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
    ]
)


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
    - strip a trailing ``CITY ST`` location suffix, anchored by a known US state
      code (so "WHOLEFDS MKT AUSTIN TX" and "WHOLEFDS MKT DALLAS TX" collapse);
    - strip trailing store-number / reference tokens (``#1234``, a bare digit
      run, or a short alphanumeric ref like ``F1234``).

    The state code anchors location stripping so arbitrary trailing words aren't
    dropped; the rare failure is a two-word name immediately followed by a state
    code with no city (e.g. "TEXAS ROADHOUSE TX"). Falls back to the collapsed
    description if stripping would leave nothing.
    """
    text = _PROCESSOR_PREFIX_RE.sub("", _collapse_whitespace(description))
    tokens = text.split()
    # Trailing "CITY ST" location suffix (needs name + city + state to remain).
    if len(tokens) > 2 and tokens[-1] in _US_STATES:
        tokens = tokens[:-2]
    # Trailing store-number / reference tokens.
    while len(tokens) > 1 and _TRAILING_REF_RE.match(tokens[-1]):
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
