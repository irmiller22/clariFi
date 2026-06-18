"""Pydantic schemas for request/response validation."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from src.domain import TransactionType


class TransactionBase(BaseModel):
    """Base schema for Transaction."""

    transaction_date: str = Field(..., description="Transaction date (MM/DD/YYYY)")
    post_date: str = Field(..., description="Post date (MM/DD/YYYY)")
    description: str = Field(..., description="Merchant/transaction description")
    category: str = Field(..., description="Transaction category")
    type: str = Field(..., description="Transaction type (e.g., Sale, Payment)")
    amount: Decimal = Field(..., description="Transaction amount")
    memo: str | None = Field(default="", description="Additional memo/notes")

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


# ---------------------------------------------------------------------------
# Response DTOs (what the API returns to the frontend)
# ---------------------------------------------------------------------------


class TransactionRead(BaseModel):
    """A single transaction as returned to the client.

    ``amount`` is presented as a JSON number for JS consumers; exact ``Decimal``
    arithmetic stays server-side. ``date`` is ``MM/DD/YYYY`` to match the
    frontend's existing date handling.
    """

    id: str
    date: str
    description: str
    amount: float
    category: str
    type: TransactionType


class TransactionList(BaseModel):
    """A page of transactions plus the total count before pagination."""

    transactions: list[TransactionRead]
    total: int


class AnalyticsSummary(BaseModel):
    """Aggregate spending metrics. Serialized with camelCase keys."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_spent: float
    total_income: float
    net_amount: float
    transaction_count: int
    avg_transaction_amount: float


class CategorySpendingRead(BaseModel):
    """A single category's spend, as returned to the client."""

    category: str
    amount: float
    count: int
    percentage: float


class TimelinePointRead(BaseModel):
    """Spend in one time bucket, as returned to the client."""

    date: str
    amount: float
    cumulative: float


class MonthlyTrendRead(BaseModel):
    """One month in a spend trend series. Serialized with camelCase keys."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    month: str
    amount: float
    delta: float
    pct_change: float | None
    direction: str


class CategoryTrendRead(BaseModel):
    """A per-category monthly trend series."""

    category: str
    points: list[MonthlyTrendRead]


class SpendingTrendsRead(BaseModel):
    """Month-over-month trends, overall and by category. camelCase keys."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    overall: list[MonthlyTrendRead]
    by_category: list[CategoryTrendRead]


class UploadResult(BaseModel):
    """Response for a successful CSV upload."""

    success: bool
    message: str
    transactions: list[TransactionRead]
    summary: AnalyticsSummary
