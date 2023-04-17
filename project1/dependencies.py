from fastapi import Request
from typing import Any
import psycopg
import psycopg_pool

async def get_pool(request: Request) -> psycopg.AsyncConnection[Any]:
    async with request.app.state.db_pool.connection() as conn:
        yield conn