from pydantic import BaseModel
from pydantic import validator
from typing import Generic, Optional, TypeVar

T = TypeVar('T')

class User(BaseModel):
    username: str
    password: str
    email: str

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
    @validator('email')
    def email_validator(cls, v):
        if ('@' and '.') not in v:
            raise ValueError('not correct email adress')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str

class DefualtResponseModel(BaseModel, Generic[T]):
    data: Optional[T] = None