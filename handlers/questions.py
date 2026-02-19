"""
Обработчик вопросов пользователя — пересылка куратору с проверкой приватности.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import load_config
from database import save_checkpoint
from handlers.start import notify_admin_checkpoint
import logging

router = Router()
config = load_config()
logger = logging.getLogger(__name__)


class QuestionStates(StatesGroup):
    waiting_for_question = State()


@router.callback_query(F.data == "menu_question")
async def start_question(query: CallbackQuery, state: FSMContext, bot: Bot):
    """Начать процесс задания вопроса."""
    user = query.from_user
    save_checkpoint(user.id, "MENU_QUESTION", "Нажал «Задать вопрос»")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Нажал «Задать вопрос»"
    )
    await query.answer()

    await state.set_state(QuestionStates.waiting_for_question)
    await query.message.answer(
        "✍️ Напиши свой вопрос, и я перешлю его нашему куратору.\n\n"
        "Также ты всегда можешь связаться с куратором напрямую: @helionstudio\n\n"
        "Отправь свой вопрос следующим сообщением\n"
        "(или /cancel для отмены):"
    )


@router.message(QuestionStates.waiting_for_question)
async def receive_question(message: Message, state: FSMContext, bot: Bot):
    """Получение вопроса и пересылка админу."""
    user = message.from_user
    if not user:
        return

    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Отменено. Возвращаюсь в меню.")
        return

    save_checkpoint(user.id, "QUESTION_SENT", f"Отправил вопрос куратору")

    # Проверяем, можно ли пересылать сообщения (forward privacy)
    # В Telegram API, если у пользователя скрыта пересылка,
    # при forward сообщение приходит без forward_from
    # Проверим через попытку forward

    forward_warning = False

    for admin_id in config.admin_ids:
        try:
            # Пробуем переслать
            forwarded = await bot.forward_message(
                chat_id=admin_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

            # Проверяем: если forward_from отсутствует — пересылка скрыта
            if not forwarded.forward_from:
                forward_warning = True
                # Отправляем админу дополнительное сообщение с данными
                name = user.first_name or "Без имени"
                uname = f"@{user.username}" if user.username else "нет username"
                await bot.send_message(
                    admin_id,
                    f"⚠️ У пользователя скрыта пересылка!\n"
                    f"👤 {name} ({uname})\n"
                    f"🆔 <code>{user.id}</code>\n\n"
                    f"Чтобы ответить, используйте:\n"
                    f"<code>/reply {user.id} текст</code>",
                    parse_mode="HTML"
                )

        except Exception as e:
            logger.warning(f"Не удалось переслать вопрос админу {admin_id}: {e}")

    if forward_warning:
        await message.answer(
            "✅ Вопрос отправлен куратору!\n\n"
            "⚠️ Обрати внимание: у тебя скрыта пересылка сообщений. "
            "Куратор не сможет связаться с тобой напрямую через пересланное сообщение.\n\n"
            "Рекомендуем написать куратору самостоятельно: @helionstudio"
        )
    else:
        await message.answer(
            "✅ Вопрос отправлен куратору! Он свяжется с тобой в ближайшее время.\n\n"
            "Также ты можешь написать ему напрямую: @helionstudio"
        )

    await state.clear()
