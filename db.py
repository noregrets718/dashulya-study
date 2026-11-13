import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "memory.db"
DB_PATH.parent.mkdir(exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id    INTEGER NOT NULL,
    user_name  TEXT NOT NULL,
    text       TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = connect_db()
    try:
        conn.execute(SCHEMA)
    finally:
        conn.close()


def save_message(chat_id: int, user_name: str, text: str) -> int:
    """Сохраняет сообщение и возвращает его id."""
    conn = connect_db()
    try:
        with conn:                      # commit при успехе, rollback при ошибке
            cur = conn.execute(
                "INSERT INTO messages (chat_id, user_name, text) VALUES (?, ?, ?)",
                (chat_id, user_name, text),
            )
            return cur.lastrowid
    finally:
        conn.close()

def search_messages(query: str, limit: int = 5) -> list[sqlite3.Row]:
    conn = connect_db()
    try:
        return conn.execute(
            "SELECT created_at, user_name, text FROM messages "
            r"WHERE text LIKE ? ESCAPE '\' "
            "ORDER BY id DESC LIMIT ?",
            (_like_pattern(query), limit),
        ).fetchall()
    finally:
        conn.close()

def _like_pattern(query: str) -> str:
    """Экранирует спецсимволы LIKE, чтобы % и _ искались буквально."""
    escaped = (
        query.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"

