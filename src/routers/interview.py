from fastapi import APIRouter
from src.routers.users import get_current_user
from fastapi import Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src.routers.websocet import manager

interview_router = APIRouter()


@interview_router.post('/start-interview/{interview_id}/{interview_type}/{position}/{company}')
async def interview(
        user: get_current_user(),
        interview_id: int,
        interview_type: str,
        position: str,
        company: str,
        db: Session = Depends(get_db)
):
    pass
# после перехода по этой ссылке открывается чат с ллмкой, которой предварительно уже загружен промт с типом интервью и тд, тут надо будет сохранить запрос на начало в бдшку.
