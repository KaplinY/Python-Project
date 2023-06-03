from fastapi import APIRouter, FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

DB_DSN = os.environ.get("DB_DSN")

def init_app(app: FastAPI): 
    @app.on_event("startup")
    async def startup_event():
        engine = create_async_engine(
        DB_DSN, echo = True,
        )
        app.state.db_engine = engine

        app.state.async_sessionmaker = async_sessionmaker(
        engine, expire_on_commit=False
        )