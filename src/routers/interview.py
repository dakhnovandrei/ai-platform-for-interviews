from fastapi import APIRouter
from src.routers.users import get_current_user
from fastapi import Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src.schemas import InterviewRequest, InterviewResponse
from src.models import InterviewSessions

interview_router = APIRouter()


@interview_router.post('/start-interview/', response_model=InterviewResponse)
async def interview(
        interview_data: InterviewRequest,
        user=Depends(get_current_user),
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

        return InterviewResponse(
            session_id=new_interview.interview_id,
            message=f"Сессия успешно создана. Требуется редирект на /interview/{new_interview.interview_id}"
        )
    except Exception as e:
        print(f"Ошибка в сохранении интервью в базу данных {e}")
