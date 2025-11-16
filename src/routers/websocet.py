from datetime import datetime
from src.ML.model import call_ai
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.schemas import ChatMessage
from typing import List, Dict
import asyncio
import json

chat_router = APIRouter(prefix='/ws/v1')


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, user_id: int, message: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)


manager = ConnectionManager()


@chat_router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Вызов ии:
            ai_response = await call_ai(message_data, user_id)

            response_data = {
                "type": "ai_message",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }
            await manager.send_personal_message(message=json.dumps(response_data), user_id=user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
