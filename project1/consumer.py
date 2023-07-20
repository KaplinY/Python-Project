import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy import select
from project1.db.models import Users
from project1.db.models import Percents_data
from statistics import mean 
import os
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import smtplib


MQ_DSN = os.environ.get("MQ_DSN")

async def on_message(message: AbstractIncomingMessage, session: AsyncSession):
    user_id = message.body
    user_id.decode()
    user_id = int(user_id)
    print(user_id)
    stmt = select(Users.email).where(Users.user_id == user_id)
    email = await session.scalar(stmt)
    print(email)
    stmt = select(Percents_data.percent).where(Percents_data.user_id == user_id)
    percent = await session.scalars(stmt)
    percent = percent.fetchall()
    #percent = await session.execute(stmt)
    #percent = percent.fetchall()
    print(percent)
    avg_percent = sum(percent)/len(percent)
    all_entries = len(percent)
    stmt = select(Percents_data.subtracted).where(Percents_data.user_id == user_id)
    subtracted = await session.scalars(stmt)
    subtracted = subtracted.fetchall()
    subtracted.sort()
    length = len(subtracted)
    if length % 2 == 0:
        median = (subtracted[length / 2 - 1] + subtracted[length / 2])/2
    else:
        median = subtracted[length // 2]
    result = str({"average percent":avg_percent, "all_entries":all_entries,"median of all subtractions":median})
    #sending email part
    # FROM = 'monty@python.com'
    # TO = [email] 
    # SUBJECT = "Stats"
    # TEXT = result

    # email_message = """\
    # From: %s
    # To: %s
    # Subject: %s
    
    # %s
    # """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    # server = smtplib.SMTP('myserver')
    # server.sendmail(FROM, TO, email_message)
    # server.quit()
    #end of this part
    print(result)
    return result


async def main() -> None:

    connection = await aio_pika.connect_robust(MQ_DSN)
    channel = await connection.channel()
    queue =  await channel.declare_queue("stats", durable=True)

    engine = create_async_engine(
        os.environ.get("DB_DSN"), echo = True,
    )
    async_session = async_sessionmaker(
        engine, expire_on_commit=False
    )

    async def process_message(message: AbstractIncomingMessage) -> None:
        async with message.process():
            async with async_session() as session:
                await on_message(message,session)

    await queue.consume(process_message)

    try:
        await asyncio.Future()
    finally:
        await connection.close()              

    # async def consume() -> None:
    #     async with channel_pool.acquire() as channel:
    #         await channel.set_qos(10)

    #         queue = await channel.declare_queue(
    #             "stats", durable=False, auto_delete=False,
    #         )
    #         async with async_session as session:
    #             await session.commit()
                
    #             async with queue.iterator() as queue_iter:
    #                 async for message in queue_iter:
    #                     async with message.process():
    #                         result = await on_message(message, session)
    #                         print(result)
    #                     await message.ack()

    # async with connection_pool, channel_pool:
    #     task = loop.create_task(consume())
    #     await task
    
if __name__ == "__main__":
    asyncio.run(main())