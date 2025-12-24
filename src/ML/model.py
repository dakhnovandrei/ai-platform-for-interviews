import os

import httpx
import requests
from typing import List, Dict

LLAMA_URL = os.getenv("LLAMA_URL")


class LLamaInterviewAI:
    def __init__(self, interview_type: str, position: str, company: str):
        self.interview_type = interview_type
        self.position = position
        self.company = company
        self.system_prompt = f"""
        Ты — опытный IT специалист, проводящий {self.interview_type} собеседование
        на позицию: {self.position} в компанию: {self.company}.

        Правила:
        - Общайся строго на русском языке
        - Используй профессиональный, уверенный тон
        - Вопросы должны быть релевантными позиции
        - Учитывай предыдущие ответы кандидата
        - Продолжай интервью, никогда не начинай заново
        - Не разъясняй правил кандидату
        - Если кандидат уклоняется — мягко возвращай его к теме
        - Не вставляй подсказки для модели
        """
        self.conversation_history: list[Dict] = []

    async def ask(self, user_message: str) -> str:
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        messages = [{"role": "system", "content": self.system_prompt}]
        # print(messages)
        for msg in self.conversation_history[-24:]:
            messages.append({
                "role": msg['role'],
                "content": msg["content"]
            })
        payload = {
            "model": "llama3:8b",
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.6,
                "top_p": 0.9,
                "num_ctx": 4096,
                "repeat_penalty": 1.1,
            }
        }
        # print(payload)
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(LLAMA_URL, json=payload)
                response.raise_for_status()
                ai_answer = response.json()
                print(ai_answer)
                assistant_text = ai_answer["message"]["content"]

                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_text,
                })
                return assistant_text

            except Exception as e:
                return f"Ошибка обращения к ai {e}"
