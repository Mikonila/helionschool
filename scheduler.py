"""
Планировщик отложенных сообщений:
- Напоминание через 2 часа после /start
- Предложение пройти тест через 2 дня
"""
import asyncio
import logging
from aiogram import Bot

from config import load_config
from database import (
    get_users_for_reminder, set_reminder_sent,
    get_users_for_test, set_test_sent,
    save_checkpoint
)
from keyboards import get_test_kb

logger = logging.getLogger(__name__)
config = load_config()

CHECK_INTERVAL = 60  # проверять каждые 60 секунд


async def send_reminders(bot: Bot):
    """Отправить напоминания пользователям (через 2 часа)."""
    users = get_users_for_reminder()
    for user_data in users:
        user_id = user_data["user_id"]
        first_name = user_data.get("first_name", "")
        name = first_name if first_name else "друг"
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"{name}, напоминаю о себе 🙂\n"
                    f"Скажи, интересен ли тебе наш формат обучения?\n"
                    f"У нас много полезного материала, нацеленного на быстрое и "
                    f"эффективное обучение"
                )
            )
            set_reminder_sent(user_id)
            save_checkpoint(user_id, "REMINDER_SENT", "Бот отправил напоминание (2ч)")
            logger.info(f"📨 Напоминание отправлено: {user_id}")
        except Exception as e:
            logger.warning(f"❌ Не удалось отправить напоминание {user_id}: {e}")
            set_reminder_sent(user_id)  # Всё равно помечаем, чтобы не спамить


async def send_test_offers(bot: Bot):
    """Предложить пройти тест (через 2 дня)."""
    users = get_users_for_test()
    for user_data in users:
        user_id = user_data["user_id"]
        first_name = user_data.get("first_name", "")
        name = first_name if first_name else "друг"
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f'{name}, получи первый урок из видео-курса за 1₽!\n\n'
                    f'Пройди тест "Какой ты художник?" и получи бонусный урок '
                    f'"Построение лица в аниме-стиле" 👇'
                ),
                reply_markup=get_test_kb(config)
            )
            set_test_sent(user_id)
            save_checkpoint(user_id, "TEST_OFFER_SENT", "Бот отправил предложение пройти тест (2 дня)")
            logger.info(f"📨 Предложение теста отправлено: {user_id}")
        except Exception as e:
            logger.warning(f"❌ Не удалось отправить тест {user_id}: {e}")
            set_test_sent(user_id)


async def scheduler_loop(bot: Bot):
    """Основной цикл планировщика."""
    logger.info("⏰ Планировщик запущен")
    while True:
        try:
            await send_reminders(bot)
            await send_test_offers(bot)
        except Exception as e:
            logger.error(f"❌ Ошибка в планировщике: {e}")
        await asyncio.sleep(CHECK_INTERVAL)
