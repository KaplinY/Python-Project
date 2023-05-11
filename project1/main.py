from typing import Any, List, Optional
from fastapi import FastAPI, HTTPException, status, Depends, Request
from pydantic import BaseModel
import psycopg
import psycopg_pool
import psycopg2
from datetime import datetime, timedelta
import os
import asyncio
import asyncpg
from pydantic import validator
from passlib.hash import pbkdf2_sha256
from jose import jwt, JWTError
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from project1.dependencies import get_pool, get_async_session
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import ForeignKey, String, Integer, TIMESTAMP, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager

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
    
db_meta = sa.MetaData() 

class Base(DeclarativeBase):
    metadata = db_meta 

class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(sa.BigInteger(), primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(sa.String(100), unique=True)
    password: Mapped[str] = mapped_column(sa.Text)

class Percents_data(Base):
    __tablename__ = "percents_data"

    id: Mapped[int] = mapped_column(sa.BigInteger(), primary_key=True, autoincrement=True)
    added: Mapped[float] = mapped_column(sa.Float)
    subtracted: Mapped[float] = mapped_column(sa.Float)
    percent: Mapped[float] = mapped_column(sa.Float)
    time: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    user: Mapped[Users] = relationship(Users, foreign_keys=[user_id], uselist=False)


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
    engine = create_async_engine(
    DB_DSN, echo = True,
    )
    app.state.db_engine = engine

    app.state.async_sessionmaker = async_sessionmaker(
    engine, expire_on_commit=False
    )
            
     
@app.post("/add_user")
async def add_user(item: User, session: AsyncSession = Depends(get_async_session)):

    hashed_password = pbkdf2_sha256.hash(item.password)
    new_user = Users(username = item.username, password = hashed_password)
    session.add(new_user)
    await session.commit()
    await session.flush()
    

@app.post("/authenticate_user")
async def user_login(item: User, session: AsyncSession = Depends(get_async_session)):

    stmt = select(Users.password).where(Users.username == item.username)
    hashed_password = await session.scalar(stmt)  
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
async def create_item(item: Perc, user: dict = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):

    if item.percent < 0:
        return {"message": "try positive value"}
    else:
        sum = item.value + item.percent*item.value/100
        sub = item.value - item.percent*item.value/100
        per = item.percent*item.value/100
        item_dict_result = {"added":sum, "subtracted":sub, "percent":per}

    now = datetime.now()

    stmt = select(Users.user_id).where(Users.username == user)
    user_id = await session.scalar(stmt)

    new_perc = Percents_data(added = sum, subtracted = sub, percent = per, time = now, user_id = user_id)
    session.add(new_perc)
    await session.commit()

    return item_dict_result




        