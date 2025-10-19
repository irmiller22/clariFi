"""Async context manager for database operations - ensures sessions are properly managed."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from src.models import Upload, Transaction, UploadDTO, TransactionDTO
from src.schemas import TransactionCreate
from src.database import AsyncSessionLocal


class UploadsContextManager:
    """
    Async context manager for Upload database operations.

    Ensures database sessions are properly created, committed/rolled back,
    and closed. All methods return read-only domain models after converting
    from DTOs while the session is still active.

    Usage:
        async with UploadsContextManager() as db:
            upload = await db.create_upload(transactions)
            # Session automatically committed and closed here

        # upload is read-only and safe to use
    """

    def __init__(self):
        """Initialize context manager."""
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self):
        """Enter async context - create database session."""
        self.session = AsyncSessionLocal()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit async context - commit/rollback and close session.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred

        Returns:
            False to propagate exceptions, None otherwise
        """
        try:
            if exc_type:
                # Exception occurred, rollback transaction
                await self.session.rollback()
                return False  # Propagate exception
            # No exception, commit transaction
            await self.session.commit()
        except Exception as e:
            # Commit failed, rollback
            await self.session.rollback()
            raise e
        finally:
            # Always close session
            await self.session.close()

    async def create_upload(
        self,
        transactions: List[TransactionCreate],
    ) -> Upload:
        """
        Create a new upload with transactions.

        Args:
            transactions: List of TransactionCreate schemas

        Returns:
            Read-only Upload instance
        """
        # Create UploadDTO
        upload_dto = UploadDTO(transaction_count=len(transactions))

        # Create TransactionDTOs
        for transaction_data in transactions:
            transaction_dto = TransactionDTO(
                transaction_date=transaction_data.transaction_date,
                post_date=transaction_data.post_date,
                description=transaction_data.description,
                category=transaction_data.category,
                type=transaction_data.type,
                amount=transaction_data.amount,
                memo=transaction_data.memo,
            )
            upload_dto.transactions.append(transaction_dto)

        # Save to database
        self.session.add(upload_dto)
        await self.session.flush()  # Flush to get IDs assigned

        # Eagerly load relationships before converting to domain model
        await self.session.refresh(
            upload_dto,
            attribute_names=["transactions"]
        )

        # Convert to read-only model BEFORE session closes
        upload = Upload.from_dto(upload_dto)

        return upload

    async def get_upload(self, upload_id: int) -> Optional[Upload]:
        """
        Get an upload by ID with all transactions.

        Args:
            upload_id: Upload ID

        Returns:
            Read-only Upload instance or None if not found
        """
        # Query database with eager loading of transactions
        result = await self.session.execute(
            select(UploadDTO)
            .options(selectinload(UploadDTO.transactions))
            .where(UploadDTO.id == upload_id)
        )
        upload_dto = result.scalar_one_or_none()

        if not upload_dto:
            return None

        # Convert to read-only model BEFORE session closes
        upload = Upload.from_dto(upload_dto)

        return upload

    async def get_all_uploads(self) -> List[Upload]:
        """
        Get all uploads with their transactions.

        Returns:
            List of read-only Upload instances
        """
        # Query database with eager loading of transactions
        result = await self.session.execute(
            select(UploadDTO).options(selectinload(UploadDTO.transactions))
        )
        upload_dtos = result.scalars().all()

        # Convert to read-only models BEFORE session closes
        uploads = [Upload.from_dto(dto) for dto in upload_dtos]

        return uploads

    async def get_transactions_by_upload(
        self, upload_id: int
    ) -> List[Transaction]:
        """
        Get all transactions for a specific upload.

        Args:
            upload_id: Upload ID

        Returns:
            List of read-only Transaction instances
        """
        # Query database
        result = await self.session.execute(
            select(TransactionDTO).where(TransactionDTO.upload_id == upload_id)
        )
        transaction_dtos = result.scalars().all()

        # Convert to read-only models BEFORE session closes
        transactions = [Transaction.from_dto(dto) for dto in transaction_dtos]

        return transactions
