<<<<<<< Updated upstream
def call_ai(message: str, user_id: int):
    pass
=======
import os
import requests
from typing import List, Dict

LLAMA_URL = os.getenv("LLAMA_URL")


async def call_ai(message: str, interview_type: str, position: str, company: str,
                  conversation_history: List[Dict] = None):
    system_prompt = f"""
        Ты - опытный IT специалист с огромным опытом, который проводит {interview_type} собеседование на позицию: {position}, в компанию: {company}.

        Твоя задача:
        1. Задавать релевантные вопросы по теме собеседования
        2. Анализировать ответы кандидата
        3. Давать конструктивную обратную связь
        4. Вести диалог естественно и профессионально

        Текущий контекст: {message}
        """

    messages = [{
        "role": "system",
        "content": system_prompt
    }]

    if conversation_history:
        for msg in conversation_history[-5:]:
            role = "user" if msg.get("is_user", True) else 'assistant'
            messages.append({
                "role": role,
                "content": msg.get("content", "")
            })

    messages.append({
        "role": "user",
        "content": message
    })

    payload = {
        "model": "llama3:8b",
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_ctx": 400
        }
    }

    try:
        response = requests.post(
            LLAMA_URL,
            json=payload,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()
        return result['message']['content']

    except requests.exceptions.RequestException as e:
        return f"Ошибка при обращении к AI: {e}"
>>>>>>> Stashed changes
