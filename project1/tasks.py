from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from project1.db.models import Users
from project1.db.models import Percents_data
import os
from sqlalchemy.ext.asyncio import AsyncSession
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.sql import func
from taskiq import TaskiqDepends
from project1.dependencies.dependencies import get_async_session
from project1.tkq import broker


MQ_DSN = os.environ.get("MQ_DSN")
SERVER_HOST = str(os.environ.get("SERVER_HOST"))
SERVER_PORT = os.environ.get("SERVER_PORT")

async def on_message(user_id: int, session: AsyncSession):
    stmt = select(Users.email).where(Users.user_id == user_id)
    email = await session.scalar(stmt)
    email = str(email)
    stmt = select(func.avg(Percents_data.percent),func.count(Percents_data.percent),func.percentile_cont(0.5).within_group(Percents_data.subtracted)).where(Percents_data.user_id == user_id)
    result = await session.execute(stmt)
    result = result.fetchall()
    result = result[0]
    avg_percent = result[0]
    all_entries = result[1]
    median = result[2]
    
    stats = str({"average percent":avg_percent, "all_entries":all_entries,"median of all subtractions":median})
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
    return stats

@broker.task
async def my_task(user_id: int, session: AsyncSession = TaskiqDepends(get_async_session)) -> None:
    print(user_id, session, "#" * 20)
    import logging
    logging.info("#" * 20 , user_id, session)
    await on_message(user_id, session)
