from fastapi import Request
from typing import Any
import psycopg
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager

async def get_pool(request: Request) -> psycopg.AsyncConnection[Any]:
    async with request.app.state.db_pool.connection() as conn:
        yield conn

async def get_async_session(request: Request) -> AsyncSession:
    sm: async_sessionmaker = request.app.state.async_sessionmaker
    async with sm() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            return
        
    await session.commit()