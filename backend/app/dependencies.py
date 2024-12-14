from app.models import UserInDB, TokenData, User
from app.settings.local import fake_users_db
from app.settings.local import settings

from typing import Annotated
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status


def verify_password(plain_password, hashed_password):
    print("Verifying password.")
    return settings.pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    print("Get password hash.")
    return settings.pwd_context.hash(password)


def get_user(db, username: str):
    print("Get user.")
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    print("Authenticating user.")
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    print("Creating access token.")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(settings.oauth2_scheme)]):
    print("Getting current user.")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    print("Get current active user.")
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
