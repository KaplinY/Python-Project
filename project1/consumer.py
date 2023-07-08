import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from project1.dependencies.dependencies import get_async_session
from aio_pika import connect
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy import select
from project1.db.models import Users
from project1.db.models import Percents_data
from statistics import mean 
import os
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import smtplib


MQ_DSN = os.environ.get("MQ_DSN")

engine = create_async_engine(
        os.environ.get("DB_DSN"), echo = True,
        )
async_sessionmaker = async_sessionmaker(
        engine, expire_on_commit=False
        )

async def get_session():
    async with async_sessionmaker as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            return

async def on_message(message: AbstractIncomingMessage) -> None:
    
    user_id = message.body
    user_id.decode()
    user_id = int(user_id)
    stmt = select(Users.email).where(Users.user_id == user_id)
    email = await session.scalar(stmt)
    session = get_session()

    stmt = select(Percents_data.percent).where(Percents_data.user_id == user_id)
    percent = await session.scalar(stmt)
    avg_percent = mean(percent)
    all_entries = len(percent)
    stmt = select(Percents_data.subtracted).where(Percents_data.user_id == user_id)
    subtracted = await session.scalar(stmt)
    subtracted.sort()
    length = len(subtracted)
    if length % 2 == 0:
        median = (subtracted[length / 2 - 1] + subtracted[length / 2])/2
    else:
        median = subtracted[length // 2]
    result = str({"average percent":avg_percent, "all_entries":all_entries,"median of all subtractions":median})

    FROM = 'monty@python.com'
    TO = [email] 
    SUBJECT = "Stats"
    TEXT = result

    message = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    server = smtplib.SMTP('myserver')
    server.sendmail(FROM, TO, message)
    server.quit()
    
    return result


async def main() -> None:

    loop = asyncio.get_event_loop()

    async def get_connection() -> AbstractRobustConnection:
        return await aio_pika.connect_robust(MQ_DSN)
    
    connection_pool: Pool = Pool(get_connection, max_size=2, loop=loop)

    async def get_channel() -> aio_pika.Channel:
        async with connection_pool.acquire() as connection:
            return await connection.channel()

    channel_pool: Pool = Pool(get_channel, max_size=10, loop=loop)

    async with channel_pool.acquire() as channel:

        queue = await channel.declare_queue(
            "stats", durable=False, auto_delete=False,
        )
        new_message = await queue.consume(on_message, no_ack=True)
    
if __name__ == "__main__":
    asyncio.run(main())