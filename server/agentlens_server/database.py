"""SQLAlchemy async engine and session management. Tables are auto-created on startup."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from agentlens_server.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_all_tables() -> None:
    """Create all database tables if they don't exist. Called on server startup."""
    # Import all models so their tables are registered with Base.metadata before create_all
    from agentlens_server.models import session  # noqa: F401
    from agentlens_server.models import trace_event  # noqa: F401
    from agentlens_server.models import memory_entry  # noqa: F401
    from agentlens_server.models import hallucination_alert  # noqa: F401
    from agentlens_server.models.budget_rule import BudgetRule  # noqa: F401
    from agentlens_server.models.prompt import Prompt  # noqa: F401
    from agentlens_server.models.prompt_version import PromptVersion  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Apply incremental column additions for SQLite (ALTER TABLE IF NOT EXISTS is not
        # supported before SQLite 3.37, so we check pragma and add missing columns manually)
        await conn.run_sync(_apply_column_migrations)


def _apply_column_migrations(conn) -> None:  # type: ignore[no-untyped-def]
    """Apply missing column additions to existing tables (safe to re-run)."""
    import logging
    _log = logging.getLogger(__name__)

    # Map of table → [(column_name, column_def)]
    _migrations = {
        "sessions": [
            ("agent_id", "TEXT"),
            ("agent_role", "TEXT"),
            ("parent_agent_id", "TEXT"),
            ("parent_session_id", "TEXT REFERENCES sessions(id)"),
        ],
        "trace_events": [],
    }

    for table, columns in _migrations.items():
        try:
            existing = {row[1] for row in conn.execute(  # type: ignore[attr-defined]
                __import__("sqlalchemy").text(f"PRAGMA table_info({table})")
            )}
            for col_name, col_def in columns:
                if col_name not in existing:
                    conn.execute(__import__("sqlalchemy").text(  # type: ignore[attr-defined]
                        f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"
                    ))
                    _log.info("Migration: added column %s.%s", table, col_name)
        except Exception as exc:
            _log.warning("Migration skipped for %s: %s", table, exc)


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
