"""
Клавиатуры бота — inline и reply.
"""
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from config import Config


# ─── Главное меню (inline) ───────────────────────────────────

def get_main_menu(config: Config) -> InlineKeyboardMarkup:
    """Главное меню бота (после /start и по кнопке Меню)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="О школе Helion 🖌", callback_data="menu_about")],
        [InlineKeyboardButton(
            text="Заказать иллюстрацию 👩‍🎨",
            callback_data="menu_order_illustration"
        )],
        [
            InlineKeyboardButton(text="Задать вопрос", callback_data="menu_question"),
            InlineKeyboardButton(text="Сотрудничество", callback_data="menu_cooperation"),
        ],
        [InlineKeyboardButton(
            text="Полезные статьи для художников",
            url=config.link_vk_community
        )],
        [InlineKeyboardButton(text="Онлайн-урок с художником", callback_data="menu_online_lesson")],
        [InlineKeyboardButton(text="🎁 Подарочный сертификат", callback_data="menu_gift_certificate")],
        [InlineKeyboardButton(text="Получить туториал и шпаргалку 🎨", callback_data="menu_tutorial")],
    ])


# ─── Воронка «О школе» ──────────────────────────────────────

def get_trial_lesson_kb(config: Config) -> InlineKeyboardMarkup:
    """Кнопка «Пройти урок» после рассказа о школе."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Пройти урок",
            url=config.link_trial_lesson
        )],
        [InlineKeyboardButton(
            text="Перейти на страницу курса",
            url=config.link_course_page
        )],
    ])


def get_want_to_draw_kb() -> InlineKeyboardMarkup:
    """Вопрос «Хотелось бы тебе научиться рисовать так же?»"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да!", callback_data="funnel_yes_draw")],
        [InlineKeyboardButton(text="Нет", callback_data="funnel_no_draw")],
    ])


def get_after_yes_kb(config: Config) -> InlineKeyboardMarkup:
    """Кнопки после положительного ответа."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Пройти пробный урок",
            url=config.link_trial_lesson
        )],
        [InlineKeyboardButton(
            text="Узнать больше про чат художников",
            callback_data="funnel_more_online"
        )],
        [InlineKeyboardButton(
            text="Узнать об онлайн-занятиях",
            callback_data="funnel_online_lessons_info"
        )],
    ])


def get_test_kb(config: Config) -> InlineKeyboardMarkup:
    """Кнопка «Пройти тест»."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пройти тест", url=config.link_test)],
    ])


def get_cancel_kb() -> InlineKeyboardMarkup:
    """Кнопка отмены записи на онлайн-урок."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_online_lesson")],
    ])


def get_cancel_gift_kb() -> InlineKeyboardMarkup:
    """Кнопка отмены оформления подарочного сертификата."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_gift_certificate")],
    ])


def get_online_lesson_payment_kb(sbp_phone: str) -> InlineKeyboardMarkup:
    """Кнопки оплаты после выбора даты урока."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💳 Оплатить по СБП",
            callback_data="show_sbp_payment"
        )],
        [InlineKeyboardButton(
            text="💬 Уточнить детали у куратора",
            url="https://t.me/helionstudio"
        )],
    ])


def get_gift_certificate_payment_kb() -> InlineKeyboardMarkup:
    """Кнопки оплаты подарочного сертификата."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💳 Оплатить по СБП",
            callback_data="show_gift_sbp_payment"
        )],
        [InlineKeyboardButton(
            text="💬 Уточнить детали у куратора",
            url="https://t.me/helionstudio"
        )],
    ])


# ─── Reply-кнопка «Меню» ────────────────────────────────────

def get_menu_reply_kb() -> ReplyKeyboardMarkup:
    """Постоянная reply-кнопка 'Меню'."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Меню ✅")]],
        resize_keyboard=True,
        is_persistent=True,
    )
