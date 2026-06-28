"""Tests for normalizing parsed CSV rows into canonical Transactions."""

from datetime import date
from decimal import Decimal

import pytest

from src.domain import Transaction
from src.schemas import TransactionCreate
from src.services.normalizer import account_from_filename, normalize, normalize_many


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
        # description keeps the original text (whitespace-collapsed); merchant is
        # canonicalized (processor prefix stripped).
        assert tx.description == "SQ *CLEVER BARBER"
        assert tx.merchant == "CLEVER BARBER"

    def test_none_memo_becomes_empty_string(self) -> None:
        assert normalize(_row(memo=None)).memo == ""


class TestMerchantCanonicalization:
    """The merchant field strips processor prefixes and store numbers."""

    def test_strips_processor_prefix(self) -> None:
        assert normalize(_row(description="TST* RESTAURANT NAME")).merchant == "RESTAURANT NAME"

    def test_strips_trailing_store_number(self) -> None:
        assert normalize(_row(description="WHOLEFDS MKT #123")).merchant == "WHOLEFDS MKT"

    def test_strips_trailing_digit_run(self) -> None:
        assert normalize(_row(description="SHELL OIL 57442197503")).merchant == "SHELL OIL"

    def test_same_merchant_different_store_numbers_match(self) -> None:
        a = normalize(_row(description="STARBUCKS STORE #111")).merchant
        b = normalize(_row(description="STARBUCKS STORE #222")).merchant
        assert a == b == "STARBUCKS STORE"

    def test_clean_name_is_unchanged(self) -> None:
        assert normalize(_row(description="TARGET")).merchant == "TARGET"

    def test_strips_alphanumeric_reference(self) -> None:
        # A short letter+digits ref (e.g. a terminal id) is stripped.
        assert normalize(_row(description="MCDONALDS F1234")).merchant == "MCDONALDS"

    def test_strips_trailing_city_state_location(self) -> None:
        assert normalize(_row(description="WHOLEFDS MKT AUSTIN TX")).merchant == "WHOLEFDS MKT"

    def test_same_merchant_different_locations_match(self) -> None:
        a = normalize(_row(description="STARBUCKS AUSTIN TX")).merchant
        b = normalize(_row(description="STARBUCKS DALLAS TX")).merchant
        assert a == b == "STARBUCKS"

    def test_strips_store_number_city_and_state_together(self) -> None:
        assert normalize(_row(description="STARBUCKS #5 AUSTIN TX")).merchant == "STARBUCKS"

    def test_bare_location_is_not_emptied(self) -> None:
        # Only a city+state with no name -> left intact rather than stripped away.
        assert normalize(_row(description="AUSTIN TX")).merchant == "AUSTIN TX"

    def test_non_location_two_letter_word_is_kept(self) -> None:
        # A trailing word that isn't a US state code must not be dropped.
        assert normalize(_row(description="JOES CRAB SHACK")).merchant == "JOES CRAB SHACK"


class TestAccountProvenance:
    """Account label is derived from the filename and carried on each txn."""

    def test_account_from_chase_filename(self) -> None:
        assert account_from_filename("Chase5168_Activity_20260626.CSV") == "5168"
        assert account_from_filename("Chase4796_Activity20260626.CSV") == "4796"

    def test_account_falls_back_to_stem(self) -> None:
        assert account_from_filename("my-export.csv") == "my-export"

    def test_account_handles_empty_filename(self) -> None:
        assert account_from_filename("") == "unknown"

    def test_normalize_sets_account(self) -> None:
        assert normalize(_row(), account="5168").account == "5168"

    def test_normalize_many_tags_all_rows(self) -> None:
        rows = [_row(description="A"), _row(description="B")]
        assert [t.account for t in normalize_many(rows, account="4796")] == ["4796", "4796"]

    def test_account_defaults_empty(self) -> None:
        assert normalize(_row()).account == ""


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
