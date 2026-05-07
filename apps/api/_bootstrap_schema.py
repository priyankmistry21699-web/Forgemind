"""Local-dev bootstrap: create_all() against the configured Postgres DB.

Run once after a fresh DB to sidestep the partially-broken migration chain.
This matches how the test suite bootstraps schema (see tests/conftest.py).
"""

import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine

from app.db.base import *  # noqa: F401, F403 — populate Base.metadata
from app.db.base_class import Base


async def main() -> None:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://forgemind:change-me@localhost:5432/forgemind",
    )
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Schema created.")


if __name__ == "__main__":
    asyncio.run(main())
