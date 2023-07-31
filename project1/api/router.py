from fastapi import APIRouter
from . import percents, users, binary_tree


router = APIRouter()
router.include_router(percents.router, prefix="/percents")
router.include_router(users.router, prefix="/users")
router.include_router(binary_tree.router, prefix="/binary_tree")