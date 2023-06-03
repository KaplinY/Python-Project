from fastapi import Depends, FastAPI
from project1.api.router import router
from project1.lifecycle import init_app

app = FastAPI()
init_app(app)
app.router.include_router(router)
