from starlette.testclient import TestClient
import pytest
from project1.app import app
from project1.db.models import db_meta
from sqlalchemy.ext.asyncio import AsyncEngine,AsyncSession,create_async_engine,async_sessionmaker,AsyncTransaction
from typing import AsyncGenerator
import os
from project1.dependencies.dependencies import get_async_session
from httpx import AsyncClient
from passlib.hash import pbkdf2_sha256
from project1.db.models import Users


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"

@pytest.fixture(scope="session")
async def _engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create engine and databases."""

    engine = create_async_engine(str(os.environ.get("DB_DSN")))
    async with engine.begin() as conn:
        await conn.run_sync(db_meta.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(db_meta.drop_all)
        await engine.dispose()


@pytest.fixture
async def dbsession(
    _engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get session to database.

    Fixture that returns a SQLAlchemy session with a SAVEPOINT, and the rollback to it
    after the test completes.
    """
    connection = await _engine.connect()
    trans = await connection.begin()

    session_maker = async_sessionmaker(
        connection,
        expire_on_commit=False,
    )
    session = session_maker()
    hashed_password = pbkdf2_sha256.hash("user!")
    new_user = Users(username = "user", password = hashed_password)
    session.add(new_user)
    await session.commit()

    try:
        yield session
    finally:
        await session.close()
        await try_rollback(trans)
        await connection.close()


async def try_rollback(rollbackable: AsyncSession | AsyncTransaction) -> None:
    """Try to rollback session."""
    try:
        await rollbackable.rollback()
    except Exception:
        return
    

@pytest.fixture(scope="function")
async def test_app(dbsession: AsyncSession):
    app.dependency_overrides[get_async_session] = lambda: dbsession

    async with AsyncClient(app = app, base_url="http://test") as client:
        yield client





