"""Domain models: DTOs for database operations and read-only domain classes."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


# ============================================================================
# DTOs (Data Transfer Objects) - SQLAlchemy models for database operations
# ============================================================================


class Base(DeclarativeBase):
    """Base class for all DTO models."""

    pass


class UploadDTO(Base):
    """DTO for Upload - used for database read/write operations."""

    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationship to transactions
    transactions: Mapped[List["TransactionDTO"]] = relationship(
        "TransactionDTO", back_populates="upload", cascade="all, delete-orphan"
    )


class TransactionDTO(Base):
    """DTO for Transaction - used for database read/write operations."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id"), nullable=False)

    # Transaction fields from Chase CSV
    transaction_date: Mapped[str] = mapped_column(String(10), nullable=False)
    post_date: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    memo: Mapped[str] = mapped_column(String(255), nullable=True, default="")

    # Relationship to upload
    upload: Mapped["UploadDTO"] = relationship("UploadDTO", back_populates="transactions")


# ============================================================================
# Read-only Domain Models - Created from DTOs after database session closes
# ============================================================================


@dataclass(frozen=True)
class Transaction:
    """Read-only Transaction domain model."""

    id: int
    upload_id: int
    transaction_date: str
    post_date: str
    description: str
    category: str
    type: str
    amount: Decimal
    memo: str

    @classmethod
    def from_dto(cls, dto: TransactionDTO) -> "Transaction":
        """
        Create a read-only Transaction from a TransactionDTO.

        Args:
            dto: TransactionDTO instance from database

        Returns:
            Read-only Transaction instance
        """
        return cls(
            id=dto.id,
            upload_id=dto.upload_id,
            transaction_date=dto.transaction_date,
            post_date=dto.post_date,
            description=dto.description,
            category=dto.category,
            type=dto.type,
            amount=dto.amount,
            memo=dto.memo,
        )


@dataclass(frozen=True)
class Upload:
    """Read-only Upload domain model."""

    id: int
    created_at: datetime
    transaction_count: int
    transactions: List[Transaction]

    @classmethod
    def from_dto(cls, dto: UploadDTO) -> "Upload":
        """
        Create a read-only Upload from an UploadDTO.

        Args:
            dto: UploadDTO instance from database

        Returns:
            Read-only Upload instance with all transactions converted
        """
        transactions = [Transaction.from_dto(t) for t in dto.transactions]
        return cls(
            id=dto.id,
            created_at=dto.created_at,
            transaction_count=dto.transaction_count,
            transactions=transactions,
        )
