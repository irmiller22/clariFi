"""Pydantic schemas for request/response validation."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional


class TransactionBase(BaseModel):
    """Base schema for Transaction."""

    transaction_date: str = Field(..., description="Transaction date (MM/DD/YYYY)")
    post_date: str = Field(..., description="Post date (MM/DD/YYYY)")
    description: str = Field(..., description="Merchant/transaction description")
    category: str = Field(..., description="Transaction category")
    type: str = Field(..., description="Transaction type (e.g., Sale, Payment)")
    amount: Decimal = Field(..., description="Transaction amount")
    memo: Optional[str] = Field(default="", description="Additional memo/notes")

    @field_validator("transaction_date", "post_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in MM/DD/YYYY format."""
        if not v:
            raise ValueError("Date cannot be empty")

        parts = v.split("/")
        if len(parts) != 3:
            raise ValueError(f"Date must be in MM/DD/YYYY format, got: {v}")

        month, day, year = parts
        if not (month.isdigit() and day.isdigit() and year.isdigit()):
            raise ValueError(f"Date components must be numeric, got: {v}")

        month_int, day_int, year_int = int(month), int(day), int(year)
        if not (1 <= month_int <= 12):
            raise ValueError(f"Month must be between 1 and 12, got: {month_int}")
        if not (1 <= day_int <= 31):
            raise ValueError(f"Day must be between 1 and 31, got: {day_int}")
        if year_int < 1900 or year_int > 2100:
            raise ValueError(f"Year must be between 1900 and 2100, got: {year_int}")

        return v

    @field_validator("description", "category", "type")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""

    pass


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    upload_id: int


class UploadResponse(BaseModel):
    """Schema for upload response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    transaction_count: int
    transactions: List[TransactionResponse]


class UploadSummary(BaseModel):
    """Schema for upload summary (without full transaction list)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    transaction_count: int
