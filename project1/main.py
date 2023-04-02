from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
import psycopg
from datetime import date
from datetime import datetime
import os
from pydantic import validator
from pydantic import ValidationError
from passlib.hash import pbkdf2_sha256

class Perc(BaseModel):
    value: float
    percent: float

class User(BaseModel):
    username: str
    password: str

    @validator('username')
    def username_validation(cls, v):
        if ' ' in v:
            raise ValueError('username contains space')
        return v
    
    @validator('password')
    def password_validation(cls, v):
        if ('!' or '&' or '$' or '%') not in v:
            raise ValueError('password should contain one of the following symbols: !,&,$,%')
        return v
    
DB_DSN = os.environ.get("DB_DSN")

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    with psycopg.connect(DB_DSN) as conn:

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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR (100) NOT NULL,
                    password VARCHAR (100) NOT NULL)
                """)
     
@app.post("/add_user")
async def add_user(item: User):

    hashed_password = pbkdf2_sha256.hash(item.password)

    with psycopg.connect(DB_DSN) as conn:

        with conn.cursor() as cur:

            cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (item.username,hashed_password)
            )
                
    pass

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

    with psycopg.connect(DB_DSN) as conn:

        with conn.cursor() as cur:
            cur.execute(
            "INSERT INTO percents_data (added, subtracted, percent, time) VALUES (%s, %s, %s, %s)",
            (item_dict_result["added"], item_dict_result["subtracted"], item_dict_result["percent"], now))


    return item_dict_result



        