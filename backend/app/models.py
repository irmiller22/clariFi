"""SQLAlchemy database models."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Upload(Base):
    """Upload model representing a CSV file upload session."""

    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationship to transactions
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="upload", cascade="all, delete-orphan"
    )


class Transaction(Base):
    """Transaction model representing a single credit card transaction."""

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
    upload: Mapped["Upload"] = relationship("Upload", back_populates="transactions")
