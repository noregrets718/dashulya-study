from dataclasses import dataclass
from enum import StrEnum


class ContinuationAction(StrEnum):
    IGNORE = "ignore"
    TEXT = "text"
    LIKE = "👍"
    HANDSHAKE = "🤝"
    HEART = "❤"
    LAUGH = "😁"
    CELEBRATE = "🎉"
    THANKS = "🙏"


@dataclass(frozen=True)
class AddressingDecision:
    should_reply: bool
    reason: str
    reaction: str | None = None