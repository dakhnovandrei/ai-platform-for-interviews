from datetime import datetime
from src.ML.model import call_ai
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from src.database import get_db
from typing import List, Dict
import json
from src.models import InterviewSessions, Messages

chat_router = APIRouter(prefix='/ws/v1')


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.conversation_history: Dict[int, List[Dict]] = {}

    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        self.active_connections[session_id] = websocket

        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []

    def disconnect(self, session_id: int):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_personal_message(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    def add_to_history(self, session_id: int, message: str, is_user: bool = True):
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []

        self.conversation_history[session_id].append({
            "content": message,
            "is_user": is_user,
            "timestamp": datetime.utcnow().isoformat()
        })

        if len(self.conversation_history) > 20:
            self.conversation_history[session_id] = self.conversation_history[session_id][-20:]

    def get_conversation_history(self, session_id: int):
        return self.conversation_history.get(session_id, [])


manager = ConnectionManager()


async def get_session_info(session_id: int, db: Session = Depends(get_db)):
    try:
        session = db.query(InterviewSessions).filter(InterviewSessions.interview_id == session_id).first()
        if session:
            return {
                "interview_type": session.interview_type,
                "position": session.position,
                "company": session.company,
                "user_id": session.user_id
            }
        return None
    except Exception as e:
        print(f'Ошибка при получении информации с базы данных {e}')


async def save_message_to_db(session_id: int, content: str, is_user: bool, db: Session = Depends(get_db)):
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
        websocket: WebSocket,
        session_id: int,
        db: Session = Depends(get_db)
):
    await manager.connect(websocket, session_id)
    try:
        session_info = await get_session_info(session_id, db)
        if not session_info:
            await websocket.close(code=1008, reason="Сессия не найдена")

        welcome_data = {
            "type": "system_message",
            "content": f"Начало {session_info["interview_type"]} собеседования на позицию: {session_info["position"]} в {session_info["company"]}",
            "timestamp": datetime.utcnow().isoformat()
        }

        await manager.send_personal_message(session_id, welcome_data)

        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_message = message_data.get("content", "").strip()
            if not user_message:
                continue

            manager.add_to_history(session_id, user_message, True)
            conv_history = manager.get_conversation_history(session_id)
            ai_response = await call_ai(user_message, session_info["interview_type"], session_info["position"],
                                        session_info["company"], conv_history[:-1])

            manager.add_to_history(session_id, ai_response, False)

            await save_message_to_db(
                session_id=session_id,
                content=user_message,
                is_user=True
            )
            await save_message_to_db(
                session_id=session_id,
                content=ai_response,
                is_user=False
            )

            response_data = {
                "type": "ai_message",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }
            await manager.send_personal_message(message=response_data, user_id=session_id)

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"Ошибка вебсокета {e}")
        manager.disconnect(session_id)
