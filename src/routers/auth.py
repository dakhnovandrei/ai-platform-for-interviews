from fastapi import HTTPException, status, Cookie, Depends
from passlib.context import CryptContext
from jose import jwt, JWTError
import os
import datetime
from pydantic import ValidationError

from src.database import get_db
from sqlalchemy.orm import Session
from src.models import Users

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_refresh_token(data: dict, expires_delta: datetime.timedelta | None = None):
    to_encode = data.copy()
    to_encode.update({"type": "refresh"})
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode.update({'exp': expire})

    return jwt.encode(to_encode, SECRET_KEY, ALGORITHM)


def create_access_token(data: dict, expires_delta: datetime.timedelta) -> str:
    to_encode = data.copy()
    to_encode.update({"type": "access"})
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, SECRET_KEY, ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(access_token: str = Cookie(None), db: Session = Depends(get_db)) -> Users:
    if not access_token:
        raise HTTPException(status_code=401, detail="Токен отсутствует")
    try:
        token = access_token.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Неверный токен")
        user = db.query(Users).filter(Users.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")

        return user
    except (JWTError, ValidationError) as e:
        raise HTTPException(status_code=401, detail="Неверный токен")
