from pydantic import BaseModel

class Percents(BaseModel):
    value: float
    percent: float