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