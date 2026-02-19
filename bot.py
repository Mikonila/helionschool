"""
Helion Bot — главный файл запуска.
Чат-бот Оливия для онлайн-школы рисования Helion.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import load_config
from database import init_db
from scheduler import scheduler_loop

# Роутеры
from handlers.questions import router as questions_router
from handlers.start import router as start_router
from handlers.menu import router as menu_router
from handlers.funnel import router as funnel_router
from handlers.admin import router as admin_router
from broadcast import router as broadcast_router

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("helion_bot.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


async def main():
    config = load_config()

    # Инициализация БД
    init_db()

    # Бот и диспетчер
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров (порядок важен!)
    # questions_router должен быть перед menu_router, т.к. он перехватывает
    # callback "menu_question" и FSM-состояние для вопроса
    dp.include_router(questions_router)
    dp.include_router(start_router)
    dp.include_router(funnel_router)
    dp.include_router(menu_router)
    dp.include_router(admin_router)
    dp.include_router(broadcast_router)

    logger.info("🚀 Бот Оливия запускается...")

    # Запускаем планировщик в фоне
    asyncio.create_task(scheduler_loop(bot))

    # Удаляем вебхук и начинаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
