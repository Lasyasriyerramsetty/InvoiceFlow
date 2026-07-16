"""Create SQLite database schema directly from SQLAlchemy models.

This script is used for local development when using SQLite instead of PostgreSQL.
It creates all tables directly from the Base metadata without requiring alembic migrations
that use PostgreSQL-specific syntax.
"""

import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.config import get_settings
from backend.app.infrastructure.database.models import Base


async def create_tables():
    settings = get_settings()
    database_url = settings.database_url

    print(f"Creating SQLite schema for: {database_url}")

    engine = create_async_engine(
        database_url,
        echo=False,
        poolclass=None,
    )

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("Schema created successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())