# tests/test_models.py  или отдельный скрипт init_db.py

import asyncio
from src.core.database import engine
from src.models.base import Base  # твой Base


async def create_tables():
    async with engine.begin() as conn:  # ← begin() возвращает AsyncConnection
        await conn.run_sync(Base.metadata.drop_all)  # сначала дроп (опционально)
        await conn.run_sync(Base.metadata.create_all)  # потом создание


if __name__ == "__main__":
    print("Creating tables...")
    asyncio.run(create_tables())
    print("Done.")
