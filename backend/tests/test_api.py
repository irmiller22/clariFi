"""Tests for UploadsContextManager."""

import pytest
from decimal import Decimal
from app.api import UploadsContextManager
from app.schemas import TransactionCreate


class TestUploadsContextManager:
    """Tests for UploadsContextManager async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_creates_and_closes_session(self):
        """Test that context manager properly creates and closes session."""
        async with UploadsContextManager() as db:
            assert db.session is not None
            # Session is active in SQLAlchemy 2.0 (implicit transaction)
            assert db.session.is_active

        # Session should be closed after exiting context
        # We can't directly check if closed, but no exception means success

    @pytest.mark.asyncio
    async def test_create_upload_with_transactions(self):
        """Test creating upload with transactions returns read-only Upload."""
        transactions = [
            TransactionCreate(
                transaction_date="10/13/2025",
                post_date="10/14/2025",
                description="Test Merchant",
                category="Shopping",
                type="Sale",
                amount=Decimal("-100.00"),
                memo="Test",
            ),
            TransactionCreate(
                transaction_date="10/14/2025",
                post_date="10/15/2025",
                description="Another Merchant",
                category="Food",
                type="Sale",
                amount=Decimal("-50.00"),
                memo="",
            ),
        ]

        async with UploadsContextManager() as db:
            upload = await db.create_upload(transactions)

        # Verify upload is read-only and accessible after session closes
        assert upload.id is not None
        assert upload.transaction_count == 2
        assert len(upload.transactions) == 2
        assert upload.transactions[0].description == "Test Merchant"
        assert upload.transactions[1].description == "Another Merchant"

    @pytest.mark.asyncio
    async def test_get_upload_by_id(self):
        """Test getting upload by ID returns read-only Upload."""
        transactions = [
            TransactionCreate(
                transaction_date="10/13/2025",
                post_date="10/14/2025",
                description="Test Merchant",
                category="Shopping",
                type="Sale",
                amount=Decimal("-100.00"),
                memo="",
            )
        ]

        # Create upload
        async with UploadsContextManager() as db:
            created_upload = await db.create_upload(transactions)
            upload_id = created_upload.id

        # Get upload in new context
        async with UploadsContextManager() as db:
            fetched_upload = await db.get_upload(upload_id)

        # Verify fetched upload
        assert fetched_upload is not None
        assert fetched_upload.id == upload_id
        assert fetched_upload.transaction_count == 1
        assert len(fetched_upload.transactions) == 1

    @pytest.mark.asyncio
    async def test_get_upload_not_found(self):
        """Test getting non-existent upload returns None."""
        async with UploadsContextManager() as db:
            upload = await db.get_upload(99999)

        assert upload is None

    @pytest.mark.asyncio
    async def test_get_all_uploads(self):
        """Test getting all uploads returns list of read-only Uploads."""
        transactions1 = [
            TransactionCreate(
                transaction_date="10/13/2025",
                post_date="10/14/2025",
                description="Merchant 1",
                category="Shopping",
                type="Sale",
                amount=Decimal("-100.00"),
                memo="",
            )
        ]
        transactions2 = [
            TransactionCreate(
                transaction_date="10/14/2025",
                post_date="10/15/2025",
                description="Merchant 2",
                category="Food",
                type="Sale",
                amount=Decimal("-50.00"),
                memo="",
            )
        ]

        # Create two uploads
        async with UploadsContextManager() as db:
            upload1 = await db.create_upload(transactions1)
            upload2 = await db.create_upload(transactions2)

        # Get all uploads
        async with UploadsContextManager() as db:
            uploads = await db.get_all_uploads()

        # Should have at least the 2 we just created
        assert len(uploads) >= 2
        assert all(upload.id is not None for upload in uploads)
        # Verify our specific uploads are in the list
        upload_ids = [u.id for u in uploads]
        assert upload1.id in upload_ids
        assert upload2.id in upload_ids

    @pytest.mark.asyncio
    async def test_get_transactions_by_upload(self):
        """Test getting transactions for specific upload."""
        transactions = [
            TransactionCreate(
                transaction_date="10/13/2025",
                post_date="10/14/2025",
                description="Merchant 1",
                category="Shopping",
                type="Sale",
                amount=Decimal("-100.00"),
                memo="",
            ),
            TransactionCreate(
                transaction_date="10/14/2025",
                post_date="10/15/2025",
                description="Merchant 2",
                category="Food",
                type="Sale",
                amount=Decimal("-50.00"),
                memo="",
            ),
        ]

        # Create upload
        async with UploadsContextManager() as db:
            upload = await db.create_upload(transactions)
            upload_id = upload.id

        # Get transactions
        async with UploadsContextManager() as db:
            txns = await db.get_transactions_by_upload(upload_id)

        assert len(txns) == 2
        assert txns[0].upload_id == upload_id
        assert txns[1].upload_id == upload_id

    @pytest.mark.asyncio
    async def test_exception_rolls_back_transaction(self):
        """Test that exceptions trigger rollback."""
        transactions = [
            TransactionCreate(
                transaction_date="10/13/2025",
                post_date="10/14/2025",
                description="Test",
                category="Shopping",
                type="Sale",
                amount=Decimal("-100.00"),
                memo="",
            )
        ]

        # Get count before error
        async with UploadsContextManager() as db:
            uploads_before = await db.get_all_uploads()
        count_before = len(uploads_before)

        with pytest.raises(ValueError):
            async with UploadsContextManager() as db:
                await db.create_upload(transactions)
                # Simulate an error after creating upload
                raise ValueError("Simulated error")

        # Verify upload was rolled back (not committed)
        async with UploadsContextManager() as db:
            uploads_after = await db.get_all_uploads()

        # Count should be the same as before (upload was rolled back)
        assert len(uploads_after) == count_before
