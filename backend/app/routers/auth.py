from app.settings import fake_users_db
from app.settings import settings
from app.models import Token
from app.dependencies import authenticate_user, create_access_token

from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/token")
async def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    print("Get token endpoint.")
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.jwt_expiration)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
