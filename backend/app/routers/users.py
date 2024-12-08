from app.models import User
from app.dependencies import get_current_active_user

from typing import Annotated
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/users", tags=["users"],)

@router.get("/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    print("Get user/me endpoint.")
    return current_user

@router.get("/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    print("get user/me/items endpoint.")
    return [{"item_id": "Foo", "owner": current_user.username}]
