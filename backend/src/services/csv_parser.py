"""CSV parser for Chase exports — auto-detects credit-card vs bank/checking.

Two Chase export shapes are supported, distinguished by their header columns:

- **Credit card**: ``Transaction Date, Post Date, Description, Category, Type,
  Amount, Memo``.
- **Bank / checking ("Activity")**: ``Details, Posting Date, Description,
  Amount, Type, Balance, Check or Slip #`` — one date, no category/memo.

Both map to the same loose ``TransactionCreate``; amounts are signed (negative
for outflows) in both, matching the domain convention.
"""

import csv
import html
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from io import StringIO

from pydantic import ValidationError

from src.schemas import TransactionCreate


class CSVParseError(Exception):
    """Exception raised when CSV parsing fails."""


def _clean(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _to_amount(value: object) -> Decimal:
    raw = _clean(value)
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid amount value: {raw!r}") from exc


def _parse_credit_card_row(row: dict) -> TransactionCreate:
    """Map a Chase credit-card export row."""
    return TransactionCreate(
        transaction_date=_clean(row.get("Transaction Date")),
        post_date=_clean(row.get("Post Date")),
        description=html.unescape(_clean(row.get("Description"))),
        category=_clean(row.get("Category")) or "Uncategorized",
        type=_clean(row.get("Type")),
        amount=_to_amount(row.get("Amount")),
        memo=_clean(row.get("Memo")),
    )


def _parse_checking_row(row: dict) -> TransactionCreate:
    """Map a Chase bank/checking 'Activity' export row.

    Checking exports carry a single Posting Date (used for both dates) and no
    Category/Memo, so category defaults to "Uncategorized".
    """
    posting_date = _clean(row.get("Posting Date"))
    return TransactionCreate(
        transaction_date=posting_date,
        post_date=posting_date,
        description=html.unescape(_clean(row.get("Description"))),
        category="Uncategorized",
        type=_clean(row.get("Type")),
        amount=_to_amount(row.get("Amount")),
        memo="",
    )


# Each known format: display name, the columns it requires, and its row mapper.
# Detection picks the first format whose required columns are all present.
_FORMATS: list[tuple[str, frozenset[str], Callable[[dict], TransactionCreate]]] = [
    (
        "Chase credit card",
        frozenset(
            {"Transaction Date", "Post Date", "Description", "Category", "Type", "Amount", "Memo"}
        ),
        _parse_credit_card_row,
    ),
    (
        "Chase bank/checking",
        frozenset({"Posting Date", "Description", "Amount", "Type"}),
        _parse_checking_row,
    ),
]


class CSVParser:
    """Parser for Chase CSV exports, auto-detecting the format by header."""

    def parse(self, csv_content: str) -> list[TransactionCreate]:
        """Parse CSV content into TransactionCreate objects.

        Raises:
            CSVParseError: empty content, unrecognized header, or a bad row.
        """
        if not csv_content or not csv_content.strip():
            raise CSVParseError("CSV content is empty")

        try:
            reader = csv.DictReader(StringIO(csv_content))
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise CSVParseError("CSV file is missing header row")

            mapper = self._select_mapper(set(fieldnames))

            transactions: list[TransactionCreate] = []
            for row_num, row in enumerate(reader, start=2):  # start at 2 (after header)
                try:
                    transactions.append(mapper(row))
                except (ValidationError, ValueError, InvalidOperation) as e:
                    raise CSVParseError(f"Error parsing row {row_num}: {e!s}") from e

            if not transactions:
                raise CSVParseError("CSV contains no transaction data")
            return transactions
        except csv.Error as e:
            raise CSVParseError(f"Invalid CSV format: {e!s}") from e

    @staticmethod
    def _select_mapper(columns: set[str]) -> Callable[[dict], TransactionCreate]:
        for _name, required, mapper in _FORMATS:
            if required <= columns:
                return mapper
        supported = ", ".join(name for name, _required, _mapper in _FORMATS)
        raise CSVParseError(
            f"Unrecognized CSV format. Header columns: {', '.join(sorted(columns))}. "
            f"Supported formats: {supported}."
        )
