from fastapi import APIRouter
from . import percents, users


router = APIRouter()
router.include_router(percents.router, prefix="/percents")
router.include_router(users.router, prefix="/users")
