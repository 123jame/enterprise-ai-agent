"""
Shared test fixtures for Library P0 Run13.

Uses an in-memory SQLite database (aiosqlite) for fast, isolated tests.
Overrides the DATABASE_URL via environment variable before importing config.
"""

import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator

# ── Force test database before ANY backend module is imported ──
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_library.db"
os.environ["DEBUG"] = "false"
os.environ["DATABASE_ECHO"] = "false"

# Ensure backend/ is on sys.path so we can import app modules
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import Base, get_db, engine as live_engine, async_session_factory as live_factory


# ── Create a dedicated test engine / session factory ──
TEST_DATABASE_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override the `get_db` dependency to use the test database."""
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Apply the override for all tests
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session")
async def prepare_database():
    """Create all tables once per test session."""
    async with test_engine.begin() as conn:
        from models import book, reader, borrowing  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(prepare_database):
    """Clean all rows between tests (autouse)."""
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient pointed at the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
