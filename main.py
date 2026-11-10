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
    host=os.getenv("AG2_BASE_URL", "http://localhost:11434"),
    # Можно не указывать: ollama-SDK сам прочитает OLLAMA_API_KEY из окружения
    api_key=os.getenv("OLLAMA_API_KEY"),
    streaming=True,
    temperature=0.2,
)
agent = Agent(
    "assistant",
    prompt="You are a helpful assistant.",
    config=config,
)


async def main() -> None:
    reply = await agent.ask("What's the weather in Paris?")
    print(reply.body)


asyncio.run(main())
