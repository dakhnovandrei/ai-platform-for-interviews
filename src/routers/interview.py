from fastapi import APIRouter
from src.routers.users import get_current_user
from fastapi import Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src.schemas import InterviewRequest
from src.models import InterviewSessions, Messages
from src.ML.model import call_ai

interview_router = APIRouter()


@interview_router.post('/start-interview/{interview_id}/{interview_type}/{position}/{company}')
async def interview(
        user: Depends(get_current_user),
        interview_data: InterviewRequest,
        db: Session = Depends(get_db)
):
    try:
        new_interview = InterviewSessions(
            user_id=user.user_id,
            job_position=interview_data.job_position,
            company=interview_data.company,
            interview_type=interview_data.interview_type
        )
        db.add(new_interview)
        db.commit()
        db.refresh(new_interview)

        first_message = await call_ai(
            message="Начни собеседование с приветствия и уточнения по готовности",
            interview_type=interview_data.interview_type,
            position=interview_data.job_position,
            company=interview_data.company
        )
        message = Messages(
            session_id=new_interview.interview_id,
            content=first_message,
            is_user=False
        )
        db.add(message)
        db.commit()
        return {
            "session_id": new_interview.interview_id,
            "first_message": first_message
        }
    except Exception as e:
        print(f"Ошибка в сохранении интервью в базу данных {e}")
