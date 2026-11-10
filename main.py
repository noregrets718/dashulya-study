import asyncio
import os

from dotenv import load_dotenv
from ag2 import Agent
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
agent = Agent(
    "assistant",
    prompt="Ты — остроумный ассистент. Отвечаешь по-русски, коротко и дерзко, без подобострастия. Не боишься поспорить, если собеседник неправ, но признаёшь свои ошибки прямо. Обычный ответ — 1–3 предложения, по делу.",
    config=config,
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
