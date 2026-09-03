from __future__ import annotations

from pathlib import Path
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from research_finder.config.settings import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if "sqlite" in settings.database_url:
            db_path_str = settings.database_url.split("///")[-1]
            if db_path_str and db_path_str != ":memory:":
                Path(db_path_str).parent.mkdir(parents=True, exist_ok=True)
            connect_args = {"timeout": 60}

        _engine = create_async_engine(settings.database_url, connect_args=connect_args, echo=False)

        if "sqlite" in settings.database_url:
            @event.listens_for(_engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA busy_timeout=60000;")
                cursor.close()

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def init_db() -> None:
    import research_finder.database.models  # noqa: F401 - ensure models are registered

    engine = get_engine()
    async with engine.begin() as conn:
        if "sqlite" in get_settings().database_url:
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            await conn.exec_driver_sql("PRAGMA busy_timeout=60000;")
        await conn.run_sync(Base.metadata.create_all)


class get_session:
    """Context manager for database sessions."""

    def __init__(self) -> None:
        self.session_factory = get_session_factory()
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self.session = self.session_factory()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()
