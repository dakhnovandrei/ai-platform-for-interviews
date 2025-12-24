import json
import logging
import os

import jwt
from starlette import status

from src.models import Users
from src.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from datetime import timedelta
from sqlalchemy.orm import Session
from src.routers.auth import create_access_token, create_refresh_token, pwd_context, get_current_user, decode_token
from dotenv import load_dotenv
from src.schemas import UserCreate, AuthResponse, UserLogin, AnalysisList, UserResponse

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))

router = APIRouter()

logger = logging.getLogger("uvicorn")  # использовать логгер Uvicorn
logger.setLevel(logging.INFO)


@router.post("/reg", tags=["Auth"])
def register(user: UserCreate, db: Session = Depends(get_db)):
    exist_user = db.query(Users).filter(Users.email == user.email).first()

    if exist_user:
        raise HTTPException(status_code=401, detail="Пользователь уже зарегистрирован")
    hashed_password = pwd_context.hash(user.password)
    new_user = Users(
        email=user.email,
        username=user.username,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "User_id": new_user.user_id}


@router.post("/login", summary="login in account")
def login(users: UserLogin, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(Users).filter(Users.email == users.email).first()
    logger.info(user)
    if not user or not pwd_context.verify(users.password, user.password):
        raise HTTPException(status_code=401, detail="Неправильная почта или пароль")

    access_token = create_access_token(
        data={'sub': user.email, 'id': user.user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = create_refresh_token(
        data={'sub': user.email, 'id': user.user_id},
        expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,
        samesite="lax",
    )

    response.set_cookie(
        key="refresh_token",
        value=f"Bearer {refresh_token}",
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,
        samesite="lax",
    )

    return AuthResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/profile/{user_id}", summary="profile base page", response_model=UserResponse)
def profile(user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_id_to_lookup = current_user.user_id if user_id is None else user_id
    user = db.query(Users).filter(Users.user_id == user_id_to_lookup).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post('/retry', summary="create new access from refresh token", response_model=AuthResponse)
def retry(response: Response, refresh_token: str = Cookie(..., alias='refresh_token')):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token не найден")

    try:
        payload = decode_token(refresh_token)
        email = payload.get('sub')
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неправильный рефреш токен")

        access_token = create_access_token(data={"sub": email},
                                           expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        new_refresh_token = create_refresh_token(data={"sub": email},
                                                 expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=False,
            samesite='lax',
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        response.set_cookie(
            key="refresh_token",
            value=f"Bearer {new_refresh_token}",
            httponly=True,
            secure=False,
            samesite='lax',
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        return AuthResponse(access_token=access_token, refresh_token=new_refresh_token)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Рефреш токен просрочен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный рефреш токен")


@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.get('/me')
async def me(user=Depends(get_current_user)):
    return user

