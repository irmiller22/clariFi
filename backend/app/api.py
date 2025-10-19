"""API for interacting with domain models - ensures database sessions are closed properly."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.models import Upload, Transaction, UploadDTO, TransactionDTO
from app.schemas import TransactionCreate


async def create_upload(
    db: AsyncSession,
    transactions: List[TransactionCreate],
) -> Upload:
    """
    Create a new upload with transactions.

    Database session is closed after converting DTO to read-only Upload.

    Args:
        db: Database session
        transactions: List of TransactionCreate schemas

    Returns:
        Read-only Upload instance (session already closed)
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
    db.add(upload_dto)
    await db.flush()  # Flush to get IDs assigned
    await db.refresh(upload_dto)  # Refresh to load relationships

    # Convert to read-only model BEFORE closing session
    upload = Upload.from_dto(upload_dto)

    # Session will be closed by the get_db dependency
    return upload


async def get_upload(db: AsyncSession, upload_id: int) -> Optional[Upload]:
    """
    Get an upload by ID with all transactions.

    Database session is closed after converting DTO to read-only Upload.

    Args:
        db: Database session
        upload_id: Upload ID

    Returns:
        Read-only Upload instance or None if not found
    """
    # Query database
    result = await db.execute(
        select(UploadDTO).where(UploadDTO.id == upload_id)
    )
    upload_dto = result.scalar_one_or_none()

    if not upload_dto:
        return None

    # Convert to read-only model BEFORE closing session
    upload = Upload.from_dto(upload_dto)

    # Session will be closed by the get_db dependency
    return upload


async def get_all_uploads(db: AsyncSession) -> List[Upload]:
    """
    Get all uploads with their transactions.

    Database session is closed after converting DTOs to read-only Uploads.

    Args:
        db: Database session

    Returns:
        List of read-only Upload instances
    """
    # Query database
    result = await db.execute(select(UploadDTO))
    upload_dtos = result.scalars().all()

    # Convert to read-only models BEFORE closing session
    uploads = [Upload.from_dto(dto) for dto in upload_dtos]

    # Session will be closed by the get_db dependency
    return uploads


async def get_transactions_by_upload(
    db: AsyncSession, upload_id: int
) -> List[Transaction]:
    """
    Get all transactions for a specific upload.

    Database session is closed after converting DTOs to read-only Transactions.

    Args:
        db: Database session
        upload_id: Upload ID

    Returns:
        List of read-only Transaction instances
    """
    # Query database
    result = await db.execute(
        select(TransactionDTO).where(TransactionDTO.upload_id == upload_id)
    )
    transaction_dtos = result.scalars().all()

    # Convert to read-only models BEFORE closing session
    transactions = [Transaction.from_dto(dto) for dto in transaction_dtos]

    # Session will be closed by the get_db dependency
    return transactions
