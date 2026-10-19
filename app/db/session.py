from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Normalize dialect prefix for asyncpg
db_url = str(settings.DATABASE_URL)
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

async_engine = create_async_engine(
    db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Export under both common conventions
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
AsyncSessionLocal = async_session_factory

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
