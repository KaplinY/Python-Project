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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.sql import func


MQ_DSN = os.environ.get("MQ_DSN")
SERVER_HOST = str(os.environ.get("SERVER_HOST"))
SERVER_PORT = int(os.environ.get("SERVER_PORT"))

async def on_message(message: AbstractIncomingMessage, session: AsyncSession):
    user_id = message.body
    user_id.decode()
    user_id = int(user_id)
    stmt = select(Users.email).where(Users.user_id == user_id)
    email = await session.scalar(stmt)
    email = str(email)
    stmt = select(func.avg(Percents_data.percent)).where(Percents_data.user_id == user_id)
    avg_percent = await session.scalar(stmt)
    stmt = select(func.count(Percents_data.percent)).where(Percents_data.user_id == user_id)
    all_entries = await session.scalar(stmt)
    stmt = select(Percents_data.subtracted).where(Percents_data.user_id == user_id).group_by(Percents_data.subtracted)
    subtracted = await session.scalars(stmt)
    subtracted = subtracted.fetchall()
    
    #percent = await session.execute(stmt)
    #percent = percent.fetchall()
    length = len(subtracted)
    if length % 2 == 0:
        median = (subtracted[length // 2 - 1] + subtracted[length // 2])/2
    else:
        median = subtracted[length // 2]
    median = str(median)
    result = str({"average percent":avg_percent, "all_entries":all_entries,"median of all subtractions":median})
    #sending email part
    msg = MIMEMultipart()
 
    html = """
    <h1 style="text-align: center;"><span style="color: #ff6800;"><strong>Requested statistics</strong></span></h1>
    <p>Average percent of all calculations: %s</p>
    <hr>
    <p>All entries: %s</p>
    <hr>
    <p>Median of all subtractions: %s</p>
    <p>&nbsp;</p>
    """%(avg_percent, all_entries, median)

    msg.attach(MIMEText(html, 'html'))
    
    # setup the parameters of the message 
    msg['From'] = "kaplin999@yandex.ru"
    msg['To'] = email
    msg['Subject'] = "User's stats"
 
    server = smtplib.SMTP(SERVER_HOST,SERVER_PORT)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()
    #end of this part
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
    
if __name__ == "__main__":
    asyncio.run(main())