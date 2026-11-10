import asyncio
import os
import random

from dotenv import load_dotenv
from ag2 import Agent, tool
from ag2.config import OllamaConfig

load_dotenv()


config = OllamaConfig(
    model=os.getenv("AG2_MODEL", "gemma4:31b"),
    # Нативный API Ollama (путь /api/chat), поэтому НЕ /v1:
    # для облака — https://ollama.com, для локального сервера — http://localhost:11434
    host=os.getenv("AG2_BASE_URL", "https://ollama.com"),
    # Можно не указывать: ollama-SDK сам прочитает OLLAMA_API_KEY из окружения
    api_key=os.getenv("OLLAMA_API_KEY"),
    streaming=True,
    temperature=0.2,
)
@tool
async def roll_dice(sides: int = 6) -> int:
    """Roll a die and return a random integer.

    Call this whenever the outcome must be unpredictable: a dice roll, a coin
    flip substitute, a random number for a game, or "pick a number up to N".

    Args:
        sides: Number of faces, any integer >= 1. Defaults to 6 (a standard die).
            Pass 100 for a range of 1..100.

    Returns:
        An integer from 1 to `sides` inclusive. Each call is independent of
        the previous ones.
    """
    return random.randint(1, sides)

agent = Agent(
    "assistant",
    prompt="Ты — остроумный ассистент. Отвечаешь по-русски, коротко и дерзко, без подобострастия. Не боишься поспорить, если собеседник неправ, но признаёшь свои ошибки прямо. Обычный ответ — 1–3 предложения, по делу. Use the roll_dice tool when the user asks to roll dice.",
    config=config,
    tools=[roll_dice]
)




async def main() -> None:
    reply = None
    while True:
        question = input("> ")
        if not question or question == "exit":
            return
        if question == "/clear":
            reply = None
            print("Контекст сброшен.")
            continue
        if reply is None:
            reply = await agent.ask(question)   # новый разговор
        else:
            reply = await reply.ask(question)   # продолжение
        print(reply.body)



asyncio.run(main())
