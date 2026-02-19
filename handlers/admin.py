"""
Админ-команды: рассылка, ответ пользователю, статистика.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command

from config import load_config
from database import (
    get_user_summary, get_all_users_count, get_all_users, get_user
)
import logging

router = Router()
config = load_config()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


@router.message(Command("reply"))
async def cmd_reply(message: Message, bot: Bot):
    """
    Ответить пользователю от лица бота.
    Формат: /reply USER_ID текст сообщения
    """
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("⛔️ У тебя нет доступа к этой команде.")
        return

    if not message.text:
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "❌ Формат: <code>/reply USER_ID текст сообщения</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ USER_ID должен быть числом.")
        return

    reply_text = parts[2]

    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=f"💬 Ответ от куратора:\n\n{reply_text}"
        )
        await message.answer(f"✅ Сообщение отправлено пользователю {target_user_id}")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить: {e}")


@router.message(Command("user"))
async def cmd_user_info(message: Message):
    """
    Информация о пользователе.
    Формат: /user USER_ID
    """
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("⛔️ У тебя нет доступа к этой команде.")
        return

    if not message.text:
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ Формат: <code>/user USER_ID</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ USER_ID должен быть числом.")
        return

    summary = get_user_summary(target_user_id)
    await message.answer(summary)


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика по пользователям."""
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("⛔️ У тебя нет доступа к этой команде.")
        return

    total = get_all_users_count()
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: {total}",
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_admin_help(message: Message):
    """Помощь по админ-командам."""
    if not message.from_user or not is_admin(message.from_user.id):
        return

    await message.answer(
        "🔧 <b>Команды администратора:</b>\n\n"
        "📢 /broadcast — Создать рассылку\n"
        "💬 /reply USER_ID текст — Ответить пользователю\n"
        "👤 /user USER_ID — Информация о пользователе\n"
        "📊 /stats — Статистика\n"
        "❓ /help — Эта справка",
        parse_mode="HTML"
    )
