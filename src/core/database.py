from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost:5432/messenger",
    echo=True
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
