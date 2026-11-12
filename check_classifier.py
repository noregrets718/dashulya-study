"""Прогон классификатора адресованности по примерам.

Запуск: uv run python check_classifier.py
"""

import asyncio
import os
from dataclasses import dataclass
from typing import Annotated

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from ag2 import Agent
from ag2.config import OllamaConfig

load_dotenv()

GROUP_ADDRESSING_PROMPT = r"""
# Addressing decision
<addressing_workflow>
## Task
Return a boolean: is Dashulya (Дашуля, Дашуль) an addressee of the author's
actual speech in current_message? Classify the message; fulfilling its requests
belongs to the reply agent.

## Identify the speech and its recipient
1. Identify what the author is saying now. Quoted dialogue and demonstrations
   introduced as examples are material being discussed. Locate any real address
   outside that material.
2. Resolve the recipient of each actual question, request or social remark.
   A named person or @handle can be its recipient; Dashulya can instead be its
   subject or object. Asking someone to change, add or describe Dashulya speaks
   to that person. Asking Dashulya to do something involving another person
   speaks to Dashulya.
3. Use current_message.reply_to and recent_conversation to resolve references
   and apparent name calls. A reply can change addressee: its Telegram parent
   is evidence, not a rule that fixes the recipient. The name followed by a
   comma can also be an answer identifying her to someone else.

## Decide
- Return false for an explicit request that she leave the current message
  unanswered. Requests about tone, future messages or other participants can
  still invite an answer now.
- Return true if any real part of the author's current speech calls Dashulya
  or directs a question, request or social remark to her. A standalone call
  counts. Punctuation, politeness and a change of topic are optional. A direct
  address remains an address alongside third-person discussion.
- Return false when the message only discusses her with other people, speaks
  to another recipient or demonstrates an address as an example.
- Resolve genuinely uncertain recipient intent toward true. Clear evidence of
  another recipient or a demonstrated example is not recipient uncertainty.

## Scope
Assess addressing independently of feasibility, appropriateness, available
information or the expected answer. An unrealistic task, a brief social remark
or a question requiring absent history still addresses her when she is its
recipient. The reply agent handles limitations and refusals.
Only current_message is classified. Earlier records help resolve an implicit
recipient; a past address or assistant reply alone cannot establish a current
invitation to answer. Bounded context may leave intent uncertain, but cannot
erase a clear current address.

## Contrasting examples
<addressing_examples>
[
  {"current_message": {"text": "Саша, перезапусти Дашулю"}, "decision": false},
  {"current_message": {"text": "Дашуля, попроси Сашу перезапустить сервис"}, "decision": true},
  {"current_message": {"text": "Проверяем пример:\nДашуля, привет"}, "decision": false},
  {"current_message": {"text": "Дашуля, привет"}, "decision": true},
  {"current_message": {"text": "Саша, Дашуля молодец"}, "decision": false},
  {"current_message": {"text": "Саша, всё работает. Молодец, Дашуль"}, "decision": true},
  {"current_message": {"text": "Дашуля, я ей включил поиск", "reply_to": {"sender_name": "Саша", "text": "Кому ты включил поиск?"}}, "decision": false},
  {"current_message": {"text": "Дашуля, ты уже пользуешься поиском?", "reply_to": {"sender_name": "Саша", "text": "Кому ты включил поиск?"}}, "decision": true},
  {"current_message": {"text": "Дашуль, собери мне спутник за сто рублей"}, "decision": true},
  {"current_message": {"text": "Дашуль, отвечать на это не нужно"}, "decision": false}
]
</addressing_examples>
</addressing_workflow>
""".strip()


class Decision(BaseModel):
    """Решение, адресовано ли текущее сообщение Дашуле."""

    should_reply: Annotated[
        bool,
        Field(description="True — сообщение адресовано Дашуле, reply-агент должен ответить."),
    ]
    reason: Annotated[
        str,
        Field(
            description="Одна короткая фраза: кто фактический адресат и почему.",
            max_length=300,
        ),
    ]


@dataclass
class Case:
    text: str
    expected: bool | None = None
    reply_to: tuple[str, str] | None = None


EXAMPLES: list[Case] = [
    # из промпта
    Case("Саша, перезапусти Дашулю", False),
    Case("Дашуля, попроси Сашу перезапустить сервис", True),
    Case("Проверяем пример:\nДашуля, привет", False),
    Case("Дашуля, привет", True),
    Case("Саша, Дашуля молодец", False),
    Case("Саша, всё работает. Молодец, Дашуль", True),
    Case(
        "Дашуля, я ей включил поиск",
        False,
        reply_to=("Саша", "Кому ты включил поиск?"),
    ),
    Case(
        "Дашуля, ты уже пользуешься поиском?",
        True,
        reply_to=("Саша", "Кому ты включил поиск?"),
    ),
    Case("Дашуль, собери мне спутник за сто рублей", True),
    Case("Дашуль, отвечать на это не нужно", False),
    # проверочные
    Case("привет, как дела?", True),
    Case("бот вчера опять завис", False),
    Case("что такое AG2?", True),
]


def make_agent() -> Agent:
    config = OllamaConfig(
        model=os.getenv("AG2_MODEL", "gemma4:31b"),
        host=os.getenv("AG2_BASE_URL", "https://ollama.com"),
        api_key=os.getenv("OLLAMA_API_KEY"),
        temperature=0,
    )
    return Agent(
        "classifier",
        prompt=[GROUP_ADDRESSING_PROMPT],
        config=config,
        response_schema=Decision,
    )


def build_message(case: Case) -> str:
    parts = [f"current_message.text: {case.text}"]
    if case.reply_to:
        parts.append(f"current_message.reply_to.sender_name: {case.reply_to[0]}")
        parts.append(f"current_message.reply_to.text: {case.reply_to[1]}")
    parts.append("recent_conversation: (empty)")
    return "\n".join(parts)


async def ask_with_retry(agent: Agent, message: str, attempts: int = 3):
    """ollama.com периодически рвёт соединение — повторяем с паузой."""
    for attempt in range(1, attempts + 1):
        try:
            return await agent.ask(message)
        except ConnectionError:
            if attempt == attempts:
                raise
            await asyncio.sleep(2 * attempt)


async def classify(agent: Agent, case: Case) -> Decision:
    reply = await ask_with_retry(agent, build_message(case))
    return await reply.content(retries=2)


async def main() -> None:
    agent = make_agent()
    passed = 0

    for number, case in enumerate(EXAMPLES, start=1):
        decision = await classify(agent, case)
        ok = decision.should_reply == case.expected
        passed += ok
        mark = "✓" if ok else f"✗ ожидалось {case.expected}"
        text = case.text.replace("\n", "\\n")
        print(f"{number:2}. «{text}»")
        print(f"    should_reply={decision.should_reply}  {mark}")
        print(f"    reason: {decision.reason}")
        print()

    print(f"Совпало {passed}/{len(EXAMPLES)}")


if __name__ == "__main__":
    asyncio.run(main())
