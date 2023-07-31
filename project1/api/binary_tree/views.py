from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from project1.dependencies.dependencies import get_async_session
from project1.api.percents.views import get_current_user
from sqlalchemy import select
from project1.db.models import Users, Percents_data
from .dtos import Node, DefualtResponseModel
from typing import Optional, List

router = APIRouter(
    responses={404: {"detail": "Not found"}},
)

def binaryTreePaths(root: Optional[Node]) -> List[str]:
        if root is None:
            return []
        if root.left is None and root.right is None:
            return [str(root.data)]
        paths = []
        if root.left:
            paths += [str(root.data) + ' -> ' + path for path in binaryTreePaths(root.left)]
        if root.right:
            paths += [str(root.data) + ' -> ' + path for path in binaryTreePaths(root.right)]
        
        return paths 

@router.post("/paths")
async def binary_tree(user: dict = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    stmt = select(Users.user_id).where(Users.username == user)
    user_id = await session.scalar(stmt)
    stmt = select(Percents_data.percent).where(Percents_data.user_id == user_id)
    result = await session.scalars(stmt)
    list_for_tree = result.all()
    root = Node(0)

    for i in range(len(list_for_tree)):
        root.insert(list_for_tree[i])

    paths = binaryTreePaths(root)
    
    return DefualtResponseModel(data = paths)
    


