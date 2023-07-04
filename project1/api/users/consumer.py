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


async def on_message(message: AbstractIncomingMessage) -> None:
    
    user_id = message.body
    print (user_id) 
    return user_id


async def main(session: AsyncSession = Depends(get_async_session)) -> None:
    connection = await connect("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()

        queue = await channel.declare_queue("stats")

        user_id = await queue.consume(on_message, no_ack=True)

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
        result = {"average percent":avg_percent, "all_entries":all_entries,"median of all subtractions":median}

        await asyncio.Future()
        return(result)