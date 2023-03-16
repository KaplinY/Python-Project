from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel


class Perc(BaseModel):
    value: float
    percent: float


app = FastAPI()


@app.post("/calculate_percents")
async def create_item(item: Perc):
    if item.percent < 0:
        return {"message": "try positive value"}
    else:
        sum = item.value + item.percent*item.value/100
        sub = item.value - item.percent*item.value/100
        per = item.percent*item.value/100
        item_dict_result = [{"added":sum, "subtracted":sub, "percent":per }]
    return item_dict_result