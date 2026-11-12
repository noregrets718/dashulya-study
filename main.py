import asyncio
import os
import random
from typing import Annotated

from ag2.events import ToolCallEvent, ToolResultEvent, ToolErrorEvent
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv
from ag2 import Agent, tool, observer, AgentReply
from ag2.config import OllamaConfig
from aiogram import Bot, Dispatcher, F
from pydantic import BaseModel, Field
from prompts import GROUP_ADDRESSING_PROMPT


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


class Decision(BaseModel):
    should_reply: Annotated[
        bool,
        Field(description="True — сообщение адресовано Дашуле, reply-агент должен ответить."),
    ]


classifier = Agent(
    "classifier",
    prompt=[GROUP_ADDRESSING_PROMPT],
    config=config,
    response_schema=Decision,
)

@observer(ToolCallEvent)
def tool_call(tool: ToolCallEvent) -> None:
    print(tool.name, tool.arguments)
@observer(ToolResultEvent)
def tool_result(result: ToolResultEvent) -> None:
    print(result.result)
@observer(ToolErrorEvent)
def tool_error(error: ToolErrorEvent) -> None:
    print(error.error)




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
    tools=[roll_dice],
    observers=[tool_call, tool_result, tool_error]
)


conversations: dict[int, AgentReply] = {}
dp = Dispatcher()

@dp.message(CommandStart())                 # /start
async def cmd_start(message: Message) -> None:
    await message.answer(f"Привет, {message.from_user.first_name}!")



@dp.message(Command("clear"))                # /dice
async def cmd_clear(message: Message) -> None:
    conversations.pop(message.chat.id, None)
    await message.answer("Контекст сброшен.")

@dp.message(F.text)                         # всё остальное с текстом — эхо
async def chat(message: Message) -> None:
    if conversations.get(message.chat.id):
        saved_reply = conversations[message.chat.id]
        reply = await saved_reply.ask(message.text)

    else:
        reply = await agent.ask(message.text)
    await message.answer(reply.body)
    conversations[message.chat.id] = reply


async def main() -> None:
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    await dp.start_polling(bot)



asyncio.run(main())
