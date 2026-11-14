import asyncio
import os
from typing import Annotated

from ag2.events import ToolCallEvent, ToolResultEvent, ToolErrorEvent
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReactionTypeEmoji
from dotenv import load_dotenv
from ag2 import Agent, observer, AgentReply
from ag2.config import OllamaConfig
from aiogram import Bot, Dispatcher, F
from pydantic import BaseModel, Field, model_validator

from db import init_db, save_message
from prompts import GROUP_ADDRESSING_PROMPT,GROUP_THREAD_CONTINUATION_PROMPT
from tools import roll_dice, search_memory
from schemas import ContinuationAction, AddressingDecision



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



class Continuation(BaseModel):
    action: ContinuationAction

continuation = Agent(
    "continuation",
    prompt=[GROUP_THREAD_CONTINUATION_PROMPT],
    config=config,
    response_schema=Continuation,
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



BOT_NAME = os.getenv("BOT_NAME", "Дашуля")

agent = Agent(
    "assistant",
    prompt=f"Ты — {BOT_NAME}, остроумный ассистент. Отвечаешь по-русски, коротко и дерзко, без подобострастия. Не боишься поспорить, если собеседник неправ, но признаёшь свои ошибки прямо. Обычный ответ — 1–3 предложения, по делу. Use tools when helpful.",
    config=config,
    tools=[roll_dice, search_memory],
    observers=[tool_call, tool_result, tool_error]
)


conversations: dict[int, AgentReply] = {}
recent: dict[int, list[tuple[str, str]]] = {}

def remember(chat_id: int, role: str, text: str) -> None:
    recent.setdefault(chat_id, []).append((role, text))
    recent[chat_id] = recent[chat_id][-4:]   # оставляем последние 4


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



async def decide(message: Message) -> AddressingDecision :
    if message.reply_to_message and message.reply_to_message.from_user.id == BOT_ID:
        return AddressingDecision(True,"reply_to_bot")

    if f"@{os.getenv("BOT_USERNAME")}" in message.text.casefold():
        return AddressingDecision(True,"explicit_mention")

    if (os.getenv("BOT_NAME")).casefold() in message.text.casefold():
        # retries: при кривом ответе ag2 переспросит модель, показав ошибку схемы
        verdict = await (await classifier.ask(build_classifier_input(message))).content(retries=2)
        reason = "classifier_accepted" if verdict.decision else "classifier_rejected"
        return AddressingDecision(verdict.decision, reason)

    if message.reply_to_message:
        return AddressingDecision(False, "reply_to_other")

    if any(role == "assistant" for role, _ in recent.get(message.chat.id, [])):
        result = await (await continuation.ask(build_classifier_input(message))).content(retries=2)
        action = result.action
        if action is ContinuationAction.TEXT:
            return AddressingDecision(True, "continuation_accepted")
        if action is ContinuationAction.IGNORE:
            return AddressingDecision(False, "continuation_rejected")
        return AddressingDecision(False, "continuation_reaction", reaction=action.value)

    return AddressingDecision(False, "name_not_found")




@dp.message(F.text)                         # всё остальное с текстом — эхо
async def chat(message: Message) -> None:

    save_message(message.chat.id, message.from_user.username, message.text )
    remember(message.chat.id, "user", message.text)
    decision = await decide(message)
    if decision.reaction is not None:
        await message.react([ReactionTypeEmoji(emoji=decision.reaction)])
        print(f"reaction: {decision.reason} -> {decision.reaction}")
        return

    if not decision.should_reply:
        return


    if conversations.get(message.chat.id):
        saved_reply = conversations[message.chat.id]
        reply = await saved_reply.ask(message.text)

    else:
        reply = await agent.ask(message.text)
    await message.answer(reply.body)
    conversations[message.chat.id] = reply
    remember(message.chat.id, "assistant", reply.body or "")


async def main() -> None:
    init_db()
    await dp.start_polling(bot)


asyncio.run(main())
