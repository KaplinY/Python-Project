from pydantic import BaseModel
from typing import Generic, Optional, TypeVar

T = TypeVar('T')

class Percents(BaseModel):
    value: float
    percent: float

class DefualtResponseModel(BaseModel, Generic[T]):
    data: Optional[T] = None