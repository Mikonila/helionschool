"""
Обработчик /start — приветствие и показ главного меню.
"""
import asyncio

from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart

from config import load_config
from database import save_user, save_checkpoint, update_funnel_stage
from keyboards import get_main_menu, get_menu_reply_kb
import logging

router = Router()
config = load_config()
logger = logging.getLogger(__name__)


async def notify_admin_checkpoint(bot: Bot, user_id: int, username: str,
                                  first_name: str, action: str):
    """Отправить админу уведомление о чекпоинте."""
    name = first_name or "Без имени"
    uname = f"@{username}" if username else "нет username"
    text = (
        f"📌 <b>Чекпоинт</b>\n"
        f"👤 {name} ({uname})\n"
        f"🆔 <code>{user_id}</code>\n"
        f"🔹 {action}"
    )
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Не удалось уведомить админа {admin_id}: {e}")


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    """Команда /start — регистрация и показ меню."""
    user = message.from_user
    if not user:
        return

    # Сохраняем пользователя в БД
    save_user(user.id, user.username, user.first_name, user.last_name)
    update_funnel_stage(user.id, "start")
    save_checkpoint(user.id, "START", "Пользователь нажал /start")

    logger.info(f"👤 Новый пользователь: {user.id} ({user.first_name})")

    # Уведомление админу
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Пользователь нажал /start"
    )

    name = user.first_name or "друг"

    # Приветствие
    await message.answer(
        f"Привет, {name}!\n"
        f"Я Оливия, чат-бот Helion 🦋\n\n"
        f"Буду рада пообщаться!",
        reply_markup=get_menu_reply_kb()
    )
    await asyncio.sleep(3)

    # Меню
    await message.answer(
        "Выбери один из пунктов ниже 👇",
        reply_markup=get_main_menu(config)
    )
