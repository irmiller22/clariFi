"""Tests for Pydantic schemas."""

import pytest
from decimal import Decimal
from pydantic import ValidationError
from src.schemas import TransactionCreate, TransactionResponse


class TestTransactionCreate:
    """Tests for TransactionCreate schema."""

    def test_valid_transaction(self):
        """Test creating a valid transaction."""
        data = {
            "transaction_date": "10/13/2025",
            "post_date": "10/14/2025",
            "description": "SQ *CLEVER BARBER",
            "category": "Personal",
            "type": "Sale",
            "amount": Decimal("-45.74"),
            "memo": "",
        }
        transaction = TransactionCreate(**data)
        assert transaction.transaction_date == "10/13/2025"
        assert transaction.post_date == "10/14/2025"
        assert transaction.description == "SQ *CLEVER BARBER"
        assert transaction.category == "Personal"
        assert transaction.type == "Sale"
        assert transaction.amount == Decimal("-45.74")
        assert transaction.memo == ""

    def test_transaction_with_memo(self):
        """Test transaction with memo field."""
        data = {
            "transaction_date": "10/13/2025",
            "post_date": "10/14/2025",
            "description": "Test Merchant",
            "category": "Shopping",
            "type": "Sale",
            "amount": Decimal("-100.00"),
            "memo": "Test memo",
        }
        transaction = TransactionCreate(**data)
        assert transaction.memo == "Test memo"

    def test_transaction_without_memo(self):
        """Test transaction defaults to empty memo."""
        data = {
            "transaction_date": "10/13/2025",
            "post_date": "10/14/2025",
            "description": "Test Merchant",
            "category": "Shopping",
            "type": "Sale",
            "amount": Decimal("-100.00"),
        }
        transaction = TransactionCreate(**data)
        assert transaction.memo == ""

    def test_invalid_date_format(self):
        """Test validation fails for invalid date format."""
        data = {
            "transaction_date": "2025-10-13",  # Wrong format
            "post_date": "10/14/2025",
            "description": "Test",
            "category": "Shopping",
            "type": "Sale",
            "amount": Decimal("-100.00"),
        }
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**data)
        assert "Date must be in MM/DD/YYYY format" in str(exc_info.value)

    def test_invalid_month(self):
        """Test validation fails for invalid month."""
        data = {
            "transaction_date": "13/13/2025",  # Month 13 doesn't exist
            "post_date": "10/14/2025",
            "description": "Test",
            "category": "Shopping",
            "type": "Sale",
            "amount": Decimal("-100.00"),
        }
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**data)
        assert "Month must be between 1 and 12" in str(exc_info.value)

    def test_invalid_day(self):
        """Test validation fails for invalid day."""
        data = {
            "transaction_date": "10/32/2025",  # Day 32 doesn't exist
            "post_date": "10/14/2025",
            "description": "Test",
            "category": "Shopping",
            "type": "Sale",
            "amount": Decimal("-100.00"),
        }
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**data)
        assert "Day must be between 1 and 31" in str(exc_info.value)

    def test_empty_description(self):
        """Test validation fails for empty description."""
        data = {
            "transaction_date": "10/13/2025",
            "post_date": "10/14/2025",
            "description": "",
            "category": "Shopping",
            "type": "Sale",
            "amount": Decimal("-100.00"),
        }
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**data)
        assert "Field cannot be empty" in str(exc_info.value)

    def test_whitespace_only_category(self):
        """Test validation fails for whitespace-only category."""
        data = {
            "transaction_date": "10/13/2025",
            "post_date": "10/14/2025",
            "description": "Test",
            "category": "   ",  # Only whitespace
            "type": "Sale",
            "amount": Decimal("-100.00"),
        }
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**data)
        assert "Field cannot be empty" in str(exc_info.value)

    def test_strips_whitespace_from_strings(self):
        """Test that string fields are trimmed."""
        data = {
            "transaction_date": "10/13/2025",
            "post_date": "10/14/2025",
            "description": "  Test Merchant  ",
            "category": "  Shopping  ",
            "type": "  Sale  ",
            "amount": Decimal("-100.00"),
        }
        transaction = TransactionCreate(**data)
        assert transaction.description == "Test Merchant"
        assert transaction.category == "Shopping"
        assert transaction.type == "Sale"

    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        data = {
            "transaction_date": "10/13/2025",
            # Missing other required fields
        }
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**data)
        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "post_date" in missing_fields
        assert "description" in missing_fields
        assert "category" in missing_fields
        assert "type" in missing_fields
        assert "amount" in missing_fields
