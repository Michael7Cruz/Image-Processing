import re
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta

import jwt
from app.core.config import get_settings
from app.models.Users import Token, User, UserCreate, UserInDB
from app.core.db import users_collection
from app.dependencies.auth_utils import (
    SECRET_KEY,
    ALGORITHM,
    get_current_active_user,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response
) -> Token:
    user = authenticate_user(users_collection, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=get_settings().REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.username, "type": "access"}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "type": "refresh"}, expires_delta=refresh_token_expires
    )
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token, 
        secure=False, # IMPORTANT: Set to True in production with HTTPS
        httponly=True, 
        samesite="lax",
        max_age=int(refresh_token_expires.total_seconds())
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/refresh")
async def refresh_token(refresh_token: str | None = Cookie(default=None)):

    if refresh_token is None:
        raise HTTPException(
            status_code=401,
            detail="Missing refresh token"
        )

    try:
        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Refresh token expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    new_access_token = create_access_token(
        data={
            "sub": user_id,
            "type": "access"
        },
        expires_delta=timedelta(
            minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@router.post("/create/", response_model = User, status_code = status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    # check if username is already used (case-insensitive)
    existing_user = users_collection.find_one({"username":{"$regex":re.compile(user.username, re.IGNORECASE)}})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    # check for existing email (case-insensitive)
    existing_email = users_collection.find_one({"email":{"$regex":re.compile(user.email, re.IGNORECASE)}})
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail = "Email already registered")
    
    hashed_password = get_password_hash(user.password)
    userInDB = UserInDB(
        username = user.username,
        full_name = user.full_name,
        disabled = user.disabled,
        email = user.email,
        hashed_password = hashed_password,
        images = []
    )
    try:
        users_collection.insert_one(userInDB.model_dump())
    except Exception as e:
        print(e)

    return userInDB

@router.get("/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user

@router.get("/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]