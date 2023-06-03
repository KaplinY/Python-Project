from pydantic import BaseModel
from pydantic import validator

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

class Token(BaseModel):
    access_token: str
    token_type: str