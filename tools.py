import random

from ag2 import tool
from db import search_messages

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

@tool(timeout=10)
def search_memory(query: str, limit: int = 5) -> str:
    """Search earlier chat messages for text containing `query`.

    Call this when you need to recall what was said before: names, preferences,
    promises, facts, or your own earlier answers. Returns the newest matches
    first, formatted as "date — author: text".

    Args:
        query: Substring to look for. Keep it short: one name, one word, or
            a short phrase. Case-insensitive for Latin text.
        limit: How many matches to return, 1..20. Defaults to 5.

    Returns:
        One line per match, newest first, e.g.
        "2026-11-10 09:12 — Саша: привет". Returns a short "nothing found"
        sentence when there are no matches.
    """
    query = query.strip()
    if not query:
        return "Empty query: nothing to search for."

    limit = max(1, min(20, limit))          # модель любит присылать 0 и 1000
    rows = search_messages(query, limit)
    if not rows:
        return f"No messages found containing {query!r}."

    return "\n".join(
        f"{row['created_at'][:16]} — {row['user_name']}: {row['text']}"
        for row in rows
    )

