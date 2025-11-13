import json
import logging
import os
from src.models import Users
from src.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from datetime import timedelta
from sqlalchemy.orm import Session
from src.routers.auth import create_access_token, create_refresh_token, pwd_context, get_current_user
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
    print(hashed_password)
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
        data={'sub': user.email, },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = create_refresh_token(
        data={'sub': user.email, },
        expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=True,
        samesite="lax",
    )

    response.set_cookie(
        key="refresh_token",
        value=f"Bearer {refresh_token}",
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        secure=True,
        samesite="lax",
    )

    return AuthResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/profile/{user_id}", summary="profile base page", response_model=UserResponse)
def profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
