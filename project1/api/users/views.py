from fastapi import HTTPException, status, Depends
from datetime import datetime, timedelta
from passlib.hash import pbkdf2_sha256
from jose import jwt
from project1.dependencies.dependencies import get_async_session
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import APIRouter
from .dtos import User, Token
from project1.db.models import Users

SECRET_KEY = "3cb260cf64fd0180f386da0e39d6c226137fe9abf98b738a70e4299e4c2afc93"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(
    responses={404: {"description": "Not found"}},
)

db_meta = sa.MetaData() 

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

@router.post("/add_user")
async def add_user(item: User, session: AsyncSession = Depends(get_async_session)):

    hashed_password = pbkdf2_sha256.hash(item.password)
    new_user = Users(username = item.username, password = hashed_password)
    session.add(new_user)
    await session.commit()
    await session.flush()
    

@router.post("/authenticate_user")
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
    return {"access_token": access_token, "token_type": "bearer"}