import asyncio
import os
from typing import Annotated

from ag2.events import ToolCallEvent, ToolResultEvent, ToolErrorEvent
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv
from ag2 import Agent, observer, AgentReply
from ag2.config import OllamaConfig
from aiogram import Bot, Dispatcher, F
from pydantic import BaseModel, Field, model_validator

from db import init_db, save_message
from prompts import GROUP_ADDRESSING_PROMPT
from tools import roll_dice, search_memory



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
    decision: Annotated[
        bool,
        Field(description="True — сообщение адресовано Дашуле, reply-агент должен ответить."),
    ]

    @model_validator(mode="before")
    @classmethod
    def _tolerant_input(cls, data: object) -> object:
        """Модель иногда отдаёт голый `true` вместо `{"decision": true}`."""
        if isinstance(data, bool):
            return {"decision": data}
        if isinstance(data, dict) and "decision" not in data:
            for key in ("should_reply", "reply", "result", "value"):
                if isinstance(data.get(key), bool):
                    return {"decision": data[key]}
            if len(data) == 1:
                (value,) = data.values()
                if isinstance(value, bool):
                    return {"decision": value}
        return data


classifier = Agent(
    "classifier",
    prompt=[GROUP_ADDRESSING_PROMPT],
    config=config,
    response_schema=Decision,
)

def build_classifier_input(message: Message) -> str:
    parts = [f"current_message.text: {message.text}"]
    if message.reply_to_message:
        original = message.reply_to_message
        sender = original.from_user.first_name if original.from_user else "unknown"
        parts.append(f"current_message.reply_to.sender_name: {sender}")
        parts.append(f"current_message.reply_to.text: {original.text}")
    parts.append("recent_conversation: (empty)")
    return "\n".join(parts)

@observer(ToolCallEvent)
def tool_call(tool: ToolCallEvent) -> None:
    print(tool.name, tool.arguments)
@observer(ToolResultEvent)
def tool_result(result: ToolResultEvent) -> None:
    print(result.result)
@observer(ToolErrorEvent)
def tool_error(error: ToolErrorEvent) -> None:
    print(error.error)





agent = Agent(
    "assistant",
    prompt="Ты — остроумный ассистент. Отвечаешь по-русски, коротко и дерзко, без подобострастия. Не боишься поспорить, если собеседник неправ, но признаёшь свои ошибки прямо. Обычный ответ — 1–3 предложения, по делу. Use the roll_dice tool when the user asks to roll dice.",
    config=config,
    tools=[roll_dice, search_memory],
    observers=[tool_call, tool_result, tool_error]
)


conversations: dict[int, AgentReply] = {}


dp = Dispatcher()
bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
BOT_ID = bot.id


@dp.message(CommandStart())                 # /start
async def cmd_start(message: Message) -> None:
    await message.answer(f"Привет, {message.from_user.first_name}!")



@dp.message(Command("clear"))                # /dice
async def cmd_clear(message: Message) -> None:
    conversations.pop(message.chat.id, None)
    await message.answer("Контекст сброшен.")



async def should_reply(message: Message) -> bool:
    if message.reply_to_message and message.reply_to_message.from_user.id == BOT_ID:
        return True
    if f"@{os.getenv("BOT_USERNAME")}" in message.text.casefold():
        return True
    if (os.getenv("BOT_NAME")).casefold() in message.text.casefold():
        # retries: при кривом ответе ag2 переспросит модель, показав ошибку схемы
        verdict = await (await classifier.ask(build_classifier_input(message))).content(retries=2)
        return verdict.decision
    return False




@dp.message(F.text)                         # всё остальное с текстом — эхо
async def chat(message: Message) -> None:
    init_db()
    save_message(message.chat.id, message.from_user.username, message.text )
    if not await should_reply(message):
        return

    if conversations.get(message.chat.id):
        saved_reply = conversations[message.chat.id]
        reply = await saved_reply.ask(message.text)

    else:
        reply = await agent.ask(message.text)
    await message.answer(reply.body)
    conversations[message.chat.id] = reply


async def main() -> None:
    await dp.start_polling(bot)


asyncio.run(main())
