from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
import psycopg
from datetime import date
from datetime import datetime

class Perc(BaseModel):
    value: float
    percent: float


app = FastAPI()


@app.post("/calculate_percents")
async def create_item(item: Perc):
    if item.percent < 0:
        return {"message": "try positive value"}
    else:
        sum = item.value + item.percent*item.value/100
        sub = item.value - item.percent*item.value/100
        per = item.percent*item.value/100
        item_dict_result = [{"added":sum, "subtracted":sub, "percent":per }]
    return item_dict_result

now = datetime.now()

with psycopg.connect("dbname=percents user=postgres") as conn:

    # Open a cursor to perform database operations
    with conn.cursor() as cur:

        # Execute a command: this creates a new table
        cur.execute("""
            CREATE TABLE [IF NOT EXISTS] percents_data (
                added FLOAT (50) NOT NULL
                subtracted FLOAT (50) NOT NULL
                percent FLOAT (50) NOT NULL
                time TIMESTAMP
            """)
        cur.execute("""
            INSERT INTO percernts_data(added, subtracted, percent, time)
            VALUES (item_dict_result["added"], item_dict_result["subtacted"], item_dict_result["percent"], now)
        """)
        