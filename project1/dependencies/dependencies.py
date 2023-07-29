from fastapi import Request
from typing import Any
import psycopg
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool
from taskiq import TaskiqDepends


async def get_pool(request: Request) -> psycopg.AsyncConnection[Any]:
    async with request.app.state.db_pool.connection() as conn:
        yield conn

async def get_async_session(request: Request = TaskiqDepends()) -> AsyncSession:
    sm: async_sessionmaker = request.app.state.async_sessionmaker
    async with sm() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            return
        
    await session.commit()

async def get_channel(request: Request) -> aio_pika.Channel:
    async with request.app.state.connection_pool.acquire() as connection:
            return await connection.channel()
    
    

    