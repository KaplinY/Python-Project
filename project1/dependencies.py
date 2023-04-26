from fastapi import Request
from typing import Any
import psycopg
from sqlalchemy.orm import Session, sessionmaker

async def get_pool(request: Request) -> psycopg.AsyncConnection[Any]:
    async with request.app.state.db_pool.connection() as conn:
        yield conn

def get_session(request: Request) -> Session:
    sm: sessionmaker = request.app.state.sessionmaker
    with sm() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            return
        
        session.commit()