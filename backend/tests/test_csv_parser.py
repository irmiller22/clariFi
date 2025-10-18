"""Tests for CSV parser service."""

import pytest
from decimal import Decimal
from io import StringIO
from app.services.csv_parser import CSVParser, CSVParseError


class TestCSVParser:
    """Tests for CSVParser class."""

    def test_parse_valid_chase_csv(self):
        """Test parsing a valid Chase CSV file."""
        csv_content = """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
10/13/2025,10/14/2025,SQ *CLEVER BARBER,Personal,Sale,-45.74,
10/13/2025,10/14/2025,FAST & FRESH BURRITO DELI,Food & Drink,Sale,-18.07,
10/12/2025,10/13/2025,Spotify USA,Bills & Utilities,Sale,-19.99,"""

        parser = CSVParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 3

        # Check first transaction
        assert transactions[0].transaction_date == "10/13/2025"
        assert transactions[0].post_date == "10/14/2025"
        assert transactions[0].description == "SQ *CLEVER BARBER"
        assert transactions[0].category == "Personal"
        assert transactions[0].type == "Sale"
        assert transactions[0].amount == Decimal("-45.74")
        assert transactions[0].memo == ""

        # Check second transaction
        assert transactions[1].description == "FAST & FRESH BURRITO DELI"
        assert transactions[1].amount == Decimal("-18.07")

    def test_parse_csv_with_html_entities(self):
        """Test that HTML entities are decoded properly."""
        csv_content = """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
10/13/2025,10/14/2025,FAST &amp; FRESH BURRITO,Food & Drink,Sale,-18.07,"""

        parser = CSVParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        assert transactions[0].description == "FAST & FRESH BURRITO"

    def test_parse_csv_with_memo(self):
        """Test parsing CSV with memo field populated."""
        csv_content = """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
10/13/2025,10/14/2025,Test Merchant,Shopping,Sale,-100.00,Important note"""

        parser = CSVParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        assert transactions[0].memo == "Important note"

    def test_parse_csv_with_positive_amount(self):
        """Test parsing CSV with positive amount (credit)."""
        csv_content = """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
10/13/2025,10/14/2025,PAYMENT - THANK YOU,Payment,Payment,500.00,"""

        parser = CSVParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        assert transactions[0].amount == Decimal("500.00")
        assert transactions[0].type == "Payment"

    def test_parse_empty_csv(self):
        """Test parsing empty CSV raises error."""
        csv_content = ""

        parser = CSVParser()
        with pytest.raises(CSVParseError) as exc_info:
            parser.parse(csv_content)
        assert "empty" in str(exc_info.value).lower()

    def test_parse_csv_without_header(self):
        """Test parsing CSV without header raises error."""
        csv_content = """10/13/2025,10/14/2025,Test,Shopping,Sale,-100.00,"""

        parser = CSVParser()
        with pytest.raises(CSVParseError) as exc_info:
            parser.parse(csv_content)
        assert "header" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

    def test_parse_csv_with_missing_columns(self):
        """Test parsing CSV with missing required columns raises error."""
        csv_content = """Transaction Date,Post Date,Description
10/13/2025,10/14/2025,Test Merchant"""

        parser = CSVParser()
        with pytest.raises(CSVParseError) as exc_info:
            parser.parse(csv_content)
        assert "column" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

    def test_parse_csv_with_invalid_date(self):
        """Test parsing CSV with invalid date format raises error."""
        csv_content = """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
2025-10-13,10/14/2025,Test,Shopping,Sale,-100.00,"""

        parser = CSVParser()
        with pytest.raises(CSVParseError) as exc_info:
            parser.parse(csv_content)
        assert "date" in str(exc_info.value).lower()

    def test_parse_csv_with_invalid_amount(self):
        """Test parsing CSV with invalid amount raises error."""
        csv_content = """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
10/13/2025,10/14/2025,Test,Shopping,Sale,not_a_number,"""

        parser = CSVParser()
        with pytest.raises(CSVParseError) as exc_info:
            parser.parse(csv_content)
        assert "amount" in str(exc_info.value).lower()

    def test_parse_csv_with_empty_required_field(self):
        """Test parsing CSV with empty required field raises error."""
        csv_content = """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
10/13/2025,10/14/2025,,Shopping,Sale,-100.00,"""

        parser = CSVParser()
        with pytest.raises(CSVParseError) as exc_info:
            parser.parse(csv_content)
        assert "empty" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_parse_large_csv(self):
        """Test parsing CSV with many transactions."""
        # Create a CSV with 100 transactions
        header = "Transaction Date,Post Date,Description,Category,Type,Amount,Memo\n"
        rows = "\n".join([
            f"10/{i%28+1}/2025,10/{i%28+1}/2025,Merchant {i},Shopping,Sale,-{i}.00,"
            for i in range(1, 101)
        ])
        csv_content = header + rows

        parser = CSVParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 100
        assert transactions[0].description == "Merchant 1"
        assert transactions[99].description == "Merchant 100"

    def test_parse_csv_strips_whitespace(self):
        """Test that whitespace is stripped from fields."""
        csv_content = """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
10/13/2025,10/14/2025,  Test Merchant  ,  Shopping  ,  Sale  ,-100.00,  Note  """

        parser = CSVParser()
        transactions = parser.parse(csv_content)

        assert transactions[0].description == "Test Merchant"
        assert transactions[0].category == "Shopping"
        assert transactions[0].type == "Sale"
        assert transactions[0].memo == "Note"
