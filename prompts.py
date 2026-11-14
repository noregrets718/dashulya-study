GROUP_ADDRESSING_PROMPT = r"""
# Addressing decision
<addressing_workflow>
## Task
Return `{"decision": true|false}` — is Dashulya (Дашуля, Дашуль) an addressee of the author's
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

GROUP_THREAD_CONTINUATION_PROMPT = """
# Choose the response to a possible continuation
<thread_continuation_workflow>
## Task and allowed outputs
Choose exactly one action for current_message:
- ignore: no response and no reaction;
- text: ask the reply agent for a necessary text answer;
- 👍: acknowledge a useful correction, confirmation or agreement;
- 🤝: acknowledge understanding, constructive feedback or reconciliation;
- ❤: warm appreciation or support;
- 😁: share a joke clearly exchanged with Dashulya;
- 🎉: congratulate a success;
- 🙏: acknowledge thanks or express gratitude.
A reaction is the complete response: the application sends it on the current
message without asking the reply agent. Choose one only when appropriate;
ignore is a normal, successful outcome. Prefer quiet participation over finding
something to add to every related remark.

## Establish whose exchange this is
This classifier receives only unnamed candidates. The application already
handles explicit mentions, name calls and direct replies to Dashulya elsewhere.
Therefore, if current_message.reply_to is not null, its parent is ANOTHER
participant or bot: choose ignore. This takes precedence over topic similarity,
shared history, the original author and an otherwise clear imperative. A task
addressed to another bot is not Dashulya's task.
For candidates without a reply parent, use the per-message authors in
recent_conversation. Only native assistant-role records are Dashulya's answers.
Asking someone about "her" is not asking her.
The same author may change recipients; another author may join her exchange,
but joining the topic alone is insufficient. Keep each claim with its recorded
speaker. A reply to someone else's statement does not correct Dashulya.

## Choose the least intrusive sufficient action
Choose text for a clear question, request or correction directed to Dashulya's
answer that actually needs new content: change the period of a summary, ask for
ready-made examples, correct a crossword constraint, clarify a misunderstood
request or ask the next concrete question in the same task. An omitted action
or object can be reconstructed from her previous answer. A direct brief social
question can also need a brief text response. Feasibility and appropriateness
are for the reply agent; an addressed request after a refusal still needs text.
Clarifying the referent of the user's own earlier request takes priority over
reaction/feedback rules: "Я про то, что я переслал" corrects a misunderstanding
of the task and selects text even without a question mark. Treat this differently
from merely evaluating her answer or suggesting an optional alternative.

Choose a reaction when the current turn clearly responds to her exchange but
only acknowledges it, thanks her, makes peace or gives feedback needing no new
explanation. Do not turn a correction into another apology or repeat her answer.
A useful small addition may warrant 👍 rather than an unsolicited research turn.
For example, "Ну да, только вместо фарша можно тушенку" after a recipe offers an
optional alternative, not a new recipe request: choose 👍 or 🤝, otherwise ignore.
A bare addition such as "А есть ещё такой протокол" or "Btw, ещё один вариант"
without asking for details selects at most 👍, otherwise ignore. It is not a
request to research or compare the new entity.
Classify ONLY the current message. An earlier unanswered question does not make
an appended acknowledgment or criticism a new request. "Я тебя такому не учил"
without a question selects 🤝 or ignore, not an explanatory text.

Choose ignore for conversations between other participants, third-person talk
about bots, quoted demonstrations, thoughts aloud, added opinions, concluding
remarks, or complaints about excessive bot activity without a request to her.
Shared subject matter, a nearby answer, technical vocabulary or a fact she could
correct are insufficient reasons for text. When recipient or need for a response
is unclear, choose ignore. Question marks alone do not establish the recipient:
"Хм, это вообще сообщение?" amid discussion of a strange forwarded message can
be a thought aloud, not a request to Dashulya. An explicit request to leave this
message unanswered also selects ignore.

## Contrastive examples
- Dashulya summarizes eight hours; the requester asks "Мало, а за 15 часов?": text.
- She lists kinds of skills; "А готовые скиллы какие знаешь?": text.
- She gives an eleven-letter answer; "Нет, там четыре буквы": text.
- She misunderstood the object; "Я про то, что я переслал": text.
- She proposes a product; "Ну короче AI жалобы?" asks whether the requester
  understood her idea: text. A short check of meaning is a real question,
  not mere agreement or a bare mention of another project.
- She greets someone; that person asks "Ты как?": text.
- Her requester says "Да, теперь понятно" or "Спасибо, помогло": 👍 or 🙏.
- A participant gives her mild constructive criticism without a new question:
  🤝, or ignore when no acknowledgment is needed.
- Someone replies to a human: "Она без упоминания умеет отвечать?": ignore.
- Someone replies to another bot: "Проверь доки и предложи твой вариант": ignore.
- Alex tells Boris "каждый в своей стране строит"; Boris replies
  "Но эти проекты публичные и конкурируют между собой": ignore.
- The next reply to Boris argues about national standards: ignore.
- A participant says "В этом-то и суть" while that human exchange continues:
  ignore, not another explanatory paragraph.
- "Кстати, есть ещё такой протокол" without asking for an explanation: at most
  👍 if clearly adding to her answer, otherwise ignore.
- "Они слишком проактивно цепляются к репликам": ignore.
</thread_continuation_workflow>
""".strip()  # ruff: ignore[ambiguous-unicode-character-string] -- Preserve Russian continuation examples.
