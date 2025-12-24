import logging
from datetime import datetime
from src.ML.model import LLamaInterviewAI
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from src.database import get_db
from typing import List, Dict

from src.models import InterviewSessions, Messages

chat_router = APIRouter(prefix='/ws/v1')


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.ai_session: Dict[int, LLamaInterviewAI] = {}

    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: int):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_personal_message(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)


manager = ConnectionManager()


async def get_session_info(session_id: int, db: Session = Depends(get_db)):
    try:
        session = db.query(InterviewSessions).filter(InterviewSessions.interview_id == session_id).first()
        if session:
            return {
                "interview_type": session.interview_type,
                "position": session.job_position,
                "company": session.company,
                "user_id": session.user_id
            }
        return None
    except Exception as e:
        print(f'Ошибка при получении информации с базы данных {e}')


async def save_message_to_db(session_id: int, content: str, is_user: bool, db: Session):
    try:
        message = Messages(
            session_id=session_id,
            content=content,
            is_user=is_user
        )
        db.add(message)
        db.commit()
    except Exception as e:
        print(f"Ошибка при добавлении сообщения в базу данных {e}")
        db.rollback()


@chat_router.websocket("/interview/{session_id}")
async def websocket_endpoint(
        session_id: int,
        websocket: WebSocket,
        db: Session = Depends(get_db)
):
    await manager.connect(websocket, session_id)
    try:
        session_info = await get_session_info(session_id, db)
        if not session_info:
            await websocket.send_json({
                'type': "error",
                "content": "Сессия не найдена"
            })
            await websocket.close(code=1008, reason="Сессия не найдена")
            return
        if session_id not in manager.ai_session:
            manager.ai_session[session_id] = LLamaInterviewAI(
                interview_type=session_info["interview_type"],
                position=session_info["position"],
                company=session_info["company"]
            )
        ai = manager.ai_session[session_id]
        await websocket.send_json({
            "type": "system_message",
            "content": f"Начало {session_info["interview_type"]} собеседования на позицию: {session_info["position"]} в {session_info["company"]}",
            "timestamp": datetime.utcnow().isoformat()
        })
        try:
            while True:
                try:
                    message_data = await websocket.receive_json()
                except WebSocketDisconnect:
                    raise
                except Exception as e:
                    print(f"ошибка в сообщении {e}")
                    continue

                user_message = message_data['content']

                try:
                    ai_response = await ai.ask(user_message)
                except Exception as e:
                    ai_response = f"ошибка лоооооол {e}"

                if not ai_response:
                    ai_response = f"Модель ничего невернула"

                await save_message_to_db(
                    session_id=session_id,
                    content=user_message,
                    is_user=True,
                    db=db
                )
                await save_message_to_db(
                    session_id=session_id,
                    content=ai_response,
                    is_user=False,
                    db=db
                )

                response_data = {
                    "type": "ai_message",
                    "content": ai_response,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_personal_message(session_id, response_data)
        except WebSocketDisconnect:
            manager.disconnect(session_id)
    except Exception as e:
        print(f"Ошибка вебсокета {e}")
        manager.disconnect(session_id)
