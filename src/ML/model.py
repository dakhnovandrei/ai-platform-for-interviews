import os
import requests

LLAMA_URL = os.getenv("LLAMA_URL")


async def call_ai(message: str, interview_type: str, position: str, company: str):
    system_prompt = f"""
        Ты - опытный IT специалист с огромным опытом, который проводит {interview_type} собеседование на позицию: {position}, в компанию: {company}.

        Твоя задача:
        1. Задавать релевантные вопросы по теме собеседования
        2. Анализировать ответы кандидата
        3. Давать конструктивную обратную связь
        4. Вести диалог естественно и профессионально

        Текущий контекст: {message}
        """
    payload = {
        "model": "llama3:8b",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
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
