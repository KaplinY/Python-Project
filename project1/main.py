from typing import Any
from fastapi import FastAPI, HTTPException, status, Depends, Request
from pydantic import BaseModel
import psycopg
import psycopg_pool
from datetime import datetime, timedelta
import os
from pydantic import validator
from passlib.hash import pbkdf2_sha256
from jose import jwt, JWTError
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from project1.dependencies import get_pool


SECRET_KEY = "3cb260cf64fd0180f386da0e39d6c226137fe9abf98b738a70e4299e4c2afc93"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

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

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(username, password, hashed_password):
    if not username:
        return False
    if not pbkdf2_sha256.verify(password, hashed_password):
        return False
    return True

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return (username)


@app.on_event("startup")
async def startup_event():
    app.state.db_pool = psycopg_pool.AsyncConnectionPool(DB_DSN, open = True,)

    async with app.state.db_pool.connection() as conn:
        conn

    # Open a cursor to perform database operations
    with psycopg.connect(DB_DSN) as conn: 

        with conn.cursor(binary = True) as cur:

        # Execute a command: this creates a new table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT PRIMARY KEY,
                    username VARCHAR (100),
                    password VARCHAR (100)
                    )
                """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS percents_data (
                    added FLOAT (50),
                    subtracted FLOAT (50),
                    percent FLOAT (50),
                    time TIMESTAMP,
                    user_id INT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE)
                """)
            
     
@app.post("/add_user")
async def add_user(item: User, db_conn: psycopg.AsyncConnection[Any] = Depends (get_pool)):

    hashed_password = pbkdf2_sha256.hash(item.password)

    async with db_conn.cursor(binary = True) as cur:
            user_id = await cur.execute("SELECT MAX(user_id) FROM users")
            user_id = await user_id.fetchone()
            user_id = user_id[0]
            if user_id == None:
                user_id = 1
            else:
                user_id = user_id + 1
            await cur.execute(
            "INSERT INTO users (user_id, username, password) VALUES (%s, %s, %s)",
            (user_id,item.username,hashed_password)
            )
                
    pass

@app.post("/authenticate_user")
async def user_login(item: User, db_conn: psycopg.AsyncConnection[Any] = Depends (get_pool)):

    async with db_conn.cursor() as cur:
        hashed_password = await cur.execute(
            "SELECT password FROM users WHERE username = %s",
            (item.username,))
        hashed_password = await hashed_password.fetchone()
        hashed_password = hashed_password[0]
            
        user = authenticate_user(item.username, item.password, hashed_password)

        if not user:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
                )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
        data={"sub": item.username}, expires_delta=access_token_expires
        )
        return {"access_tocken": access_token}
            
       

@app.post("/calculate_percents")
async def create_item(item: Perc, user: dict = Depends(get_current_user), db_conn: psycopg.AsyncConnection[Any] = Depends (get_pool)):

    if item.percent < 0:
        return {"message": "try positive value"}
    else:
        sum = item.value + item.percent*item.value/100
        sub = item.value - item.percent*item.value/100
        per = item.percent*item.value/100
        item_dict_result = {"added":sum, "subtracted":sub, "percent":per}

    now = datetime.now()

    async with db_conn.cursor() as cur:
        user_id = await cur.execute(
            "SELECT user_id FROM users WHERE username = %s",
            (user,))
        user_id = await user_id.fetchone()
        user_id = user_id[0]
        await cur.execute(
        "INSERT INTO percents_data (added, subtracted, percent, time, user_id) VALUES (%s, %s, %s, %s, %s)",
        (item_dict_result["added"], item_dict_result["subtracted"], item_dict_result["percent"], now, user_id))


    return item_dict_result




        