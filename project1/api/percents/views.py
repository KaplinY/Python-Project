from fastapi import HTTPException, status, Depends
from datetime import datetime
from jose import jwt, JWTError
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from project1.dependencies.dependencies import get_async_session
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import APIRouter, Header
from .dtos import Percents, DefualtResponseModel
from project1.db.models import Users, Percents_data

SECRET_KEY = "3cb260cf64fd0180f386da0e39d6c226137fe9abf98b738a70e4299e4c2afc93"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", scheme_name="JWT")

db_meta = sa.MetaData() 

router = APIRouter(
    responses={404: {"detail": "Not found"}},
)

async def get_current_user(token: str = Header(default=None)):
    credentials_exception = HTTPException(
        status_code=401,
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

@router.post("/calculate_percents")
async def create_item(item: Percents, user: dict = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):

    if item.percent < 0:
        raise HTTPException(
            status_code=400,
            detail="Could not process with this request",
            headers={"Error": "Try positive value"}
        )
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

    return DefualtResponseModel(data = item_dict_result)