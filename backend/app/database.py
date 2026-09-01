from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import database_ssl_required, get_settings

settings = get_settings()

_connect_args: dict = {}
if database_ssl_required(settings.database_url):
    _connect_args["ssl"] = True

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def apply_schema_patches(conn) -> None:
    """Add columns on existing Postgres tables (create_all does not alter tables)."""
    patches = [
        "ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS disease TEXT DEFAULT ''",
        "ALTER TABLE medicines ADD COLUMN IF NOT EXISTS disease VARCHAR(255) DEFAULT ''",
        "ALTER TABLE medicines ADD COLUMN IF NOT EXISTS frequency_pattern VARCHAR(30) DEFAULT 'daily'",
        "ALTER TABLE medicines ADD COLUMN IF NOT EXISTS times_per_day INTEGER DEFAULT 1",
        "ALTER TABLE medicines ADD COLUMN IF NOT EXISTS dose_times TEXT DEFAULT ''",
        "ALTER TABLE medicines ADD COLUMN IF NOT EXISTS start_time VARCHAR(10) DEFAULT ''",
        "ALTER TABLE medicines ADD COLUMN IF NOT EXISTS start_date VARCHAR(20) DEFAULT ''",
    ]
    for stmt in patches:
        await conn.execute(text(stmt))


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
