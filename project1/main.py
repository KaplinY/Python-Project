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

@app.on_event("startup")
async def startup_event():
    with psycopg.connect("dbname=percents user=postgres password=postgres") as conn:

    # Open a cursor to perform database operations
        with conn.cursor() as cur:

        # Execute a command: this creates a new table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS percents_data (
                    added FLOAT (50) NOT NULL,
                    subtracted FLOAT (50) NOT NULL,
                    percent FLOAT (50) NOT NULL,
                    time TIMESTAMP)
                """)

@app.post("/calculate_percents")
async def create_item(item: Perc):
    if item.percent < 0:
        return {"message": "try positive value"}
    else:
        sum = item.value + item.percent*item.value/100
        sub = item.value - item.percent*item.value/100
        per = item.percent*item.value/100
        item_dict_result = [{"added":sum, "subtracted":sub, "percent":per }]

    now = datetime.now()

    with psycopg.connect("dbname=percents user=postgres password=postgres") as conn:

        with conn.cursor() as cur:
            cur.execute(
            "INSERT INTO percents_data (added, subtracted, percent, time) VALUES (%s, %s, %s, %s)",
            (item_dict_result["added"], item_dict_result["subtracted"], item_dict_result["percent"], now))


    return item_dict_result



        