"""
Модуль для управления рассылкой сообщений всем пользователям.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import load_config
from database import get_all_users
import logging

router = Router()
config = load_config()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


# Состояния для FSM
class BroadcastStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()
    waiting_for_confirmation = State()


def get_preview_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для предпросмотра сообщения."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_send")],
            [InlineKeyboardButton(text="✏️ Изменить текст", callback_data="broadcast_edit_text")],
            [InlineKeyboardButton(text="🖼️ Изменить фото", callback_data="broadcast_edit_photo")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")],
        ]
    )


@router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    """Начало процесса рассылки."""
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("⛔️ У тебя нет доступа к этой команде.")
        return

    logger.info(f"✅ Админ {message.from_user.id} начал рассылку")
    await state.set_state(BroadcastStates.waiting_for_text)
    await message.answer(
        "📢 Введи текст рассылки:\n"
        "(Или отправь /cancel для отмены)"
    )


@router.message(BroadcastStates.waiting_for_text)
async def receive_text(message: Message, state: FSMContext):
    """Получение текста рассылки."""
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Рассылка отменена.")
        return

    if not message.text:
        await message.answer("⚠️ Пожалуйста, отправь текст сообщения.")
        return

    await state.update_data(text=message.text)
    await state.set_state(BroadcastStates.waiting_for_photo)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Без фото", callback_data="broadcast_no_photo")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")],
        ]
    )

    await message.answer(
        "📸 Отправь фото (или нажми кнопку, если оно не нужно):\n"
        "(Или отправь /cancel для отмены)",
        reply_markup=keyboard
    )


@router.message(BroadcastStates.waiting_for_photo)
async def receive_photo(message: Message, state: FSMContext):
    """Получение фото для рассылки."""
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Рассылка отменена.")
        return

    if message.photo:
        photo_id = message.photo[-1].file_id
        await state.update_data(photo_id=photo_id)
        await state.set_state(BroadcastStates.waiting_for_confirmation)

        data = await state.get_data()
        await show_preview(message, data)
    else:
        await message.answer("⚠️ Отправь фото или используй кнопку 'Без фото'.")


@router.callback_query(F.data == "broadcast_no_photo")
async def no_photo(query: CallbackQuery, state: FSMContext):
    """Продолжение без фото."""
    await state.set_state(BroadcastStates.waiting_for_confirmation)
    data = await state.get_data()
    await query.message.delete()
    await show_preview(query.message, data)
    await query.answer()


@router.callback_query(F.data == "broadcast_edit_text")
async def edit_text(query: CallbackQuery, state: FSMContext):
    """Вернуться к редактированию текста."""
    await query.message.delete()
    await state.set_state(BroadcastStates.waiting_for_text)
    await query.message.answer(
        "📝 Введи новый текст:\n"
        "(Или отправь /cancel для отмены)"
    )
    await query.answer()


@router.callback_query(F.data == "broadcast_edit_photo")
async def edit_photo(query: CallbackQuery, state: FSMContext):
    """Вернуться к редактированию фото."""
    await query.message.delete()
    await state.set_state(BroadcastStates.waiting_for_photo)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Без фото", callback_data="broadcast_no_photo")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")],
        ]
    )
    await query.message.answer(
        "📸 Отправь новое фото:\n"
        "(Или отправь /cancel для отмены)",
        reply_markup=keyboard
    )
    await query.answer()


@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast(query: CallbackQuery, state: FSMContext):
    """Отмена рассылки."""
    await state.clear()
    await query.message.delete()
    await query.message.answer("❌ Рассылка отменена.")
    await query.answer()


async def show_preview(message: Message, data: dict):
    """Показать предпросмотр сообщения."""
    text = data.get("text", "")
    photo_id = data.get("photo_id")

    preview_text = f"📋 <b>Предпросмотр сообщения:</b>\n\n{text}"

    if photo_id:
        await message.answer_photo(
            photo=photo_id,
            caption=preview_text,
            parse_mode="HTML",
            reply_markup=get_preview_keyboard()
        )
    else:
        await message.answer(
            preview_text,
            parse_mode="HTML",
            reply_markup=get_preview_keyboard()
        )


@router.callback_query(F.data == "broadcast_send")
async def send_broadcast(query: CallbackQuery, state: FSMContext, bot: Bot):
    """Отправить рассылку всем пользователям."""
    logger.info(f"📤 Начинаю рассылку от админа {query.from_user.id}")

    await query.message.delete()

    data = await state.get_data()
    text = data.get("text", "")
    photo_id = data.get("photo_id")

    user_ids = get_all_users()

    if not user_ids:
        await query.message.answer("⚠️ Нет пользователей для рассылки.")
        await state.clear()
        return

    sent_count = 0
    failed_count = 0

    status_message = await query.message.answer(
        f"📤 Рассылка: 0/{len(user_ids)}..."
    )

    for i, user_id in enumerate(user_ids, start=1):
        try:
            if photo_id:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=text,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=text,
                    parse_mode="HTML"
                )
            sent_count += 1
        except Exception as e:
            logger.warning(f"❌ Ошибка отправки {user_id}: {e}")
            failed_count += 1

        if i % 10 == 0:
            try:
                await status_message.edit_text(
                    f"📤 Рассылка: {i}/{len(user_ids)}..."
                )
            except:
                pass

    result_text = (
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📤 Отправлено: {sent_count}\n"
        f"❌ Ошибок: {failed_count}\n"
        f"📊 Всего: {len(user_ids)}"
    )

    logger.info(f"✅ Рассылка: отправлено {sent_count}, ошибок {failed_count}")

    await status_message.edit_text(result_text, parse_mode="HTML")
    await query.answer()
    await state.clear()
