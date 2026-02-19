"""
Модуль базы данных — SQLite для хранения пользователей и чекпоинтов.
"""
import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "helion.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Создание таблиц при первом запуске."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered_at TEXT NOT NULL,
            funnel_stage TEXT DEFAULT 'start',
            is_blocked INTEGER DEFAULT 0,
            reminder_sent INTEGER DEFAULT 0,
            test_sent INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_checkpoints_user
        ON checkpoints(user_id)
    """)

    conn.commit()
    conn.close()
    logger.info("✅ База данных инициализирована")


# ─── Пользователи ───────────────────────────────────────────

def save_user(user_id: int, username: str = None,
              first_name: str = None, last_name: str = None):
    """Сохранить или обновить пользователя."""
    conn = get_connection()
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO users (user_id, username, first_name, last_name, registered_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name
    """, (user_id, username, first_name, last_name, now))
    conn.commit()
    conn.close()


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Получить данные пользователя."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_all_users() -> List[int]:
    """Получить ID всех незаблокированных пользователей."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT user_id FROM users WHERE is_blocked = 0"
    ).fetchall()
    conn.close()
    return [r["user_id"] for r in rows]


def get_all_users_count() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE is_blocked = 0").fetchone()
    conn.close()
    return row["cnt"] if row else 0


def set_user_blocked(user_id: int, blocked: bool = True):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET is_blocked = ? WHERE user_id = ?",
        (1 if blocked else 0, user_id)
    )
    conn.commit()
    conn.close()


def update_funnel_stage(user_id: int, stage: str):
    """Обновить этап воронки."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET funnel_stage = ? WHERE user_id = ?",
        (stage, user_id)
    )
    conn.commit()
    conn.close()


def set_reminder_sent(user_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET reminder_sent = 1 WHERE user_id = ?", (user_id,)
    )
    conn.commit()
    conn.close()


def set_test_sent(user_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET test_sent = 1 WHERE user_id = ?", (user_id,)
    )
    conn.commit()
    conn.close()


def get_users_for_reminder() -> List[Dict[str, Any]]:
    """Пользователи, которым нужно отправить напоминание (>2ч, ещё не отправлено)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM users
        WHERE reminder_sent = 0
          AND is_blocked = 0
          AND datetime(registered_at) <= datetime('now', '-2 hours')
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_users_for_test() -> List[Dict[str, Any]]:
    """Пользователи, которым нужно отправить предложение пройти тест (>2 дня)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM users
        WHERE test_sent = 0
          AND is_blocked = 0
          AND datetime(registered_at) <= datetime('now', '-2 days')
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Чекпоинты ──────────────────────────────────────────────

def save_checkpoint(user_id: int, action: str, details: str = None):
    """Сохранить чекпоинт действия пользователя."""
    conn = get_connection()
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO checkpoints (user_id, action, details, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, action, details, now))
    conn.commit()
    conn.close()


def get_user_checkpoints(user_id: int) -> List[Dict[str, Any]]:
    """Получить все чекпоинты пользователя."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM checkpoints
        WHERE user_id = ?
        ORDER BY created_at ASC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_summary(user_id: int) -> str:
    """Текстовая сводка по пользователю для админа."""
    user = get_user(user_id)
    if not user:
        return f"Пользователь {user_id} не найден."

    name_parts = []
    if user.get("first_name"):
        name_parts.append(user["first_name"])
    if user.get("last_name"):
        name_parts.append(user["last_name"])
    name = " ".join(name_parts) or "Без имени"

    username = f"@{user['username']}" if user.get("username") else "нет username"

    checkpoints = get_user_checkpoints(user_id)
    cp_lines = []
    for cp in checkpoints:
        ts = cp["created_at"][:16].replace("T", " ")
        line = f"  • [{ts}] {cp['action']}"
        if cp.get("details"):
            line += f" — {cp['details']}"
        cp_lines.append(line)

    cp_text = "\n".join(cp_lines) if cp_lines else "  нет действий"

    return (
        f"👤 {name} ({username})\n"
        f"🆔 {user_id}\n"
        f"📅 Зарегистрирован: {user['registered_at'][:16].replace('T', ' ')}\n"
        f"🔹 Этап воронки: {user['funnel_stage']}\n"
        f"\n📋 Чекпоинты:\n{cp_text}"
    )
