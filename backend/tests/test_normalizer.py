"""Tests for normalizing parsed CSV rows into canonical Transactions."""

from datetime import date
from decimal import Decimal

import pytest

from src.domain import Transaction
from src.schemas import TransactionCreate
from src.services.normalizer import normalize, normalize_many


def _row(**overrides: object) -> TransactionCreate:
    """Build a validated CSV row (TransactionCreate), overriding as needed."""
    data: dict[str, object] = {
        "transaction_date": "01/05/2025",
        "post_date": "01/06/2025",
        "description": "SQ *CLEVER BARBER",
        "category": "Personal",
        "type": "Sale",
        "amount": Decimal("-45.74"),
        "memo": "",
    }
    data.update(overrides)
    return TransactionCreate(**data)


class TestDateParsing:
    """MM/DD/YYYY strings become real date objects."""

    def test_parses_transaction_and_post_dates(self) -> None:
        tx = normalize(_row(transaction_date="03/09/2025", post_date="03/11/2025"))
        assert tx.transaction_date == date(2025, 3, 9)
        assert tx.post_date == date(2025, 3, 11)

    def test_calendar_invalid_date_raises(self) -> None:
        # Feb 31 passes the schema's lenient format check but isn't a real date.
        row = _row(transaction_date="02/31/2025")
        with pytest.raises(ValueError, match="MM/DD/YYYY"):
            normalize(row)


class TestAmountAndType:
    """Amount sign is preserved exactly; type is derived from it."""

    def test_amount_is_exact_decimal(self) -> None:
        tx = normalize(_row(amount=Decimal("-45.74")))
        assert isinstance(tx.amount, Decimal)
        assert tx.amount == Decimal("-45.74")

    def test_negative_amount_is_debit(self) -> None:
        assert normalize(_row(amount=Decimal("-12.00"))).type == "debit"

    def test_positive_amount_is_credit(self) -> None:
        assert normalize(_row(amount=Decimal("250.00"))).type == "credit"


class TestDerivedAndPreservedFields:
    """Month is derived; the raw card type is preserved."""

    def test_month_key(self) -> None:
        assert normalize(_row(transaction_date="07/15/2025")).month == "2025-07"

    def test_source_type_preserved(self) -> None:
        # The raw Chase "Type" (Payment) must survive so analytics can tell a
        # card payment from real income later.
        assert normalize(_row(type="Payment", amount=Decimal("500.00"))).source_type == "Payment"


class TestStringNormalization:
    """Description/merchant whitespace is collapsed; missing memo becomes ''."""

    def test_collapses_whitespace(self) -> None:
        tx = normalize(_row(description="SQ   *CLEVER    BARBER"))
        assert tx.description == "SQ *CLEVER BARBER"
        assert tx.merchant == "SQ *CLEVER BARBER"

    def test_none_memo_becomes_empty_string(self) -> None:
        assert normalize(_row(memo=None)).memo == ""


class TestNormalizeMany:
    """normalize_many maps a list of rows, preserving order."""

    def test_maps_in_order(self) -> None:
        rows = [
            _row(description="First", amount=Decimal("-1.00")),
            _row(description="Second", amount=Decimal("-2.00")),
        ]
        result = normalize_many(rows)
        assert [t.description for t in result] == ["First", "Second"]
        assert all(isinstance(t, Transaction) for t in result)
