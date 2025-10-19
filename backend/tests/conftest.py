"""Pytest configuration and fixtures for tests."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import init_db, drop_db, engine


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Set up test database before running tests.

    Creates database and user if they don't exist.
    Runs once per test session, cleans up at the end.
    """
    # Connect to postgres database to create range database and user
    # Uses POSTGRESQL_SUPERUSER env var, defaults to current user
    import os
    import getpass

    superuser = os.getenv("POSTGRESQL_SUPERUSER", getpass.getuser())
    admin_url = f"postgresql+asyncpg://{superuser}@localhost:5432/postgres"

    admin_engine = create_async_engine(
        admin_url,
        isolation_level="AUTOCOMMIT",
    )

    try:
        async with admin_engine.begin() as conn:
            # Create user if not exists
            await conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'range') THEN "
                    "CREATE USER range WITH PASSWORD 'range'; "
                    "END IF; END $$;"
                )
            )

            # Create database if not exists
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'range'")
            )
            if not result.scalar():
                await conn.execute(text("CREATE DATABASE range OWNER range"))

    finally:
        await admin_engine.dispose()

    # Now create tables in the range database
    await init_db()

    yield

    # Cleanup only after entire test session completes
    await engine.dispose()
    await drop_db()


