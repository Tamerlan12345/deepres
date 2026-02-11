from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# --- FIX START ---
def get_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "asyncpg" not in database_url:
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url

# Автоматическая замена драйвера на асинхронный (asyncpg), 
# если платформа передала стандартный URL.
database_url = get_async_database_url(settings.DATABASE_URL)
# --- FIX END ---

engine = create_async_engine(database_url, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        # Plan-minimum: Drop tables if using SQLite (dev environment) to ensure schema is up to date
        # Check if we are using sqlite
        if "sqlite" in settings.DATABASE_URL:
            await conn.run_sync(Base.metadata.drop_all)

        await conn.run_sync(Base.metadata.create_all)
