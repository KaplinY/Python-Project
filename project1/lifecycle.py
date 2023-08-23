import uuid
from fastapi import APIRouter, FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractIncomingMessage
from aio_pika.pool import Pool
from taskiq_aio_pika import AioPikaBroker
import asyncio
from project1.tkq import broker
from project1.api.websockets.manager import manager


def init_app(app: FastAPI): 
    @app.on_event("startup")
    async def _startup_event():
        engine = create_async_engine(
        os.environ.get("DB_DSN"), echo = True,
        )
        app.state.db_engine = engine

        app.state.async_sessionmaker = async_sessionmaker(
        engine, expire_on_commit=False
        )
    @app.on_event("startup")
    async def _startup_rabbitmq():
        async def get_connection() -> AbstractRobustConnection:
            return await aio_pika.connect_robust(os.environ.get("MQ_DSN"))
        loop = asyncio.get_event_loop()
        connection_pool: Pool = Pool(get_connection, max_size = 2, loop = loop)
        app.state.connection_pool = connection_pool
        async def get_channel() -> aio_pika.Channel:
            async with connection_pool.acquire() as connection:
                return await connection.channel()
        channel_pool: Pool = Pool(get_channel, max_size=10, loop=loop)
        queue_name = "stats"
        async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
            await channel.set_qos(10)

            queue = await channel.declare_queue(
                queue_name, durable=True
            )
    @app.on_event("startup")
    async def _app_startup():
        if not broker.is_worker_process:
            await broker.startup()
    @app.on_event("startup")
    async def _start_exchange():
        connection = await aio_pika.connect_robust(url = os.environ.get("MQ_DSN"))
        channel = await connection.channel()
        exchange = await channel.declare_exchange(name = "currency", type = aio_pika.ExchangeType.FANOUT)
        queue = await channel.declare_queue(name = uuid.uuid4().hex, auto_delete=True)
        await queue.bind(exchange,routing_key=uuid.uuid4().hex)
        async def on_message(message: AbstractIncomingMessage):
            async with message.process():
                value = message.body.decode()
                await manager.broadcast(f"1$ is currently:{value}")    
        await queue.consume(callback=on_message)
        


        

            
        

        

