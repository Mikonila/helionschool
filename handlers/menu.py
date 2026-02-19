"""
Обработчики пунктов главного меню.
"""
import os
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import load_config
from database import save_checkpoint, update_funnel_stage
from keyboards import (
    get_main_menu, get_menu_reply_kb
)
from handlers.start import notify_admin_checkpoint
import logging

router = Router()
config = load_config()
logger = logging.getLogger(__name__)


class OnlineLessonStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_datetime = State()


class GiftCertificateStates(StatesGroup):
    waiting_for_recipient_name = State()


# ─── Reply-кнопка «Меню ✅» ─────────────────────────────────

@router.message(F.text == "Меню ✅")
async def reply_menu(message: Message):
    """Обработка reply-кнопки Меню."""
    user = message.from_user
    if user:
        save_checkpoint(user.id, "MENU", "Вернулся в меню")

    await message.answer(
        "Выбери из списка ниже",
        reply_markup=get_main_menu(config)
    )


# ─── О школе Helion ─────────────────────────────────────────

@router.callback_query(F.data == "menu_about")
async def menu_about(query: CallbackQuery, bot: Bot):
    """О школе Helion — запуск воронки."""
    user = query.from_user
    save_checkpoint(user.id, "MENU_ABOUT", "Нажал «О школе Helion»")
    update_funnel_stage(user.id, "about_school")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Нажал «О школе Helion»"
    )

    await query.answer()

    # Текст о школе
    await query.message.answer(
        "<b>Helion</b> — это онлайн-школа рисования в аниме-стиле, "
        "объединившая в себе <b>более 150 художников</b>, которые обучают "
        "новичков, помогают учиться на ошибках и рисовать лучше с "
        "каждым днём. Весь опыт художники передали в нашем <b>видео-курсе</b>!",
        parse_mode="HTML"
    )

    await asyncio.sleep(8)

    from keyboards import get_trial_lesson_kb
    await query.message.answer(
        "Ты можешь пройти наш пробный урок (1 видео + доп. "
        "материалы), который можно получить после регистрации на "
        "нашем сайте 👇",
        reply_markup=get_trial_lesson_kb(config)
    )

    # Отправляем работы художников (альбом)
    from aiogram.types import InputMediaPhoto
    artworks_dir = os.path.join(config.base_dir, "media", "artworks")

    # Собираем фото работ (и .jpg и .png)
    artworks_files = [
        f for f in os.listdir(artworks_dir)
        if f.endswith((".jpg", ".png"))
    ]
    # Сортируем по номеру в имени файла
    artworks_files.sort(key=lambda x: int(x.split('.')[0]))

    if artworks_files:
        media_caption = (
            "Вот некоторые <b>работы наших преподавателей и художников</b>, "
            "дающих обратную связь по работам учеников"
        )

        media_group = []
        for fname in artworks_files:
            path = os.path.join(artworks_dir, fname)
            if not media_group:
                media_group.append(
                    InputMediaPhoto(
                        media=FSInputFile(path),
                        caption=media_caption,
                        parse_mode="HTML"
                    )
                )
            else:
                media_group.append(InputMediaPhoto(media=FSInputFile(path)))

        if media_group:
            await bot.send_media_group(
                chat_id=query.message.chat.id,
                media=media_group
            )

    await asyncio.sleep(5)

    # Вопрос «Хотелось бы тебе научиться рисовать так же?»
    from keyboards import get_want_to_draw_kb
    await query.message.answer(
        "Хотелось ли бы тебе научиться рисовать так же?",
        reply_markup=get_want_to_draw_kb()
    )


# ─── Задать вопрос ──────────────────────────────────────────
# Обработка «Задать вопрос» находится в handlers/questions.py


# ─── Заказать иллюстрацию ───────────────────────────────────

@router.callback_query(F.data == "menu_order_illustration")
async def menu_order_illustration(query: CallbackQuery, bot: Bot):
    """Заказать иллюстрацию."""
    user = query.from_user
    save_checkpoint(user.id, "MENU_ORDER_ILLUSTRATION", "Нажал «Заказать иллюстрацию»")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Нажал «Заказать иллюстрацию»"
    )
    await query.answer()

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    order_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💬 Связаться с куратором",
            url="https://t.me/helionstudio"
        )]
    ])

    await query.message.answer(
        "🎨 <b>Заказать иллюстрацию</b>\n\n"
        "Наши художники создают уникальные иллюстрации в аниме-стиле!\n\n"
        "📌 <a href='https://kwork.ru/illustrations/24893278/illyustratsiya-personazha-v-anime-stile'>Мы на Кворк</a>\n"
        "📌 <a href='https://www.avito.ru/moskva/predlozheniya_uslug/anime_illyustratsiya_2536881019'>Мы на Авито</a>\n\n"
        "Для обсуждения деталей и стоимости работы свяжитесь с нашим куратором:",
        parse_mode="HTML",
        reply_markup=order_kb
    )


# ─── Сотрудничество ─────────────────────────────────────────

@router.callback_query(F.data == "menu_cooperation")
async def menu_cooperation(query: CallbackQuery, bot: Bot):
    """Сотрудничество."""
    user = query.from_user
    save_checkpoint(user.id, "MENU_COOPERATION", "Нажал «Сотрудничество»")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Нажал «Сотрудничество»"
    )
    await query.answer()

    await query.message.answer(
        "🤝 По вопросам сотрудничества обращайтесь к нашему куратору:\n\n"
        "@NPnnn28\n"
        "Мы открыты к предложениям!"
    )


# ─── Онлайн-урок с художником ───────────────────────────────

@router.callback_query(F.data == "menu_online_lesson")
async def menu_online_lesson(query: CallbackQuery, state: FSMContext, bot: Bot):
    """Онлайн-урок с художником — запрос информации."""
    user = query.from_user
    save_checkpoint(user.id, "MENU_ONLINE_LESSON", "Нажал «Онлайн-урок с художником»")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Нажал «Онлайн-урок с художником»"
    )
    await query.answer()

    await query.message.answer(
        "🎓 <b>Онлайн-занятия с художником</b>\n\n"
        "Это твой личный урок по видеосвязи с опытным преподавателем! 👨‍🎨\n\n"
        "✨ Что тебя ждёт:\n"
        "• <b>45 минут</b> персонального внимания\n"
        "• Проработка именно <b>твоих вопросов</b>\n"
        "• Ты и преподаватель рисуете на общей онлайн-доске\n"
        "• <b>Дружеская атмосфера</b> без стресса и давления\n\n"
        "💰 Стоимость: <b>1500 рублей</b>\n\n"
        "Давай запишем тебя на удобное время? 😊",
        parse_mode="HTML"
    )
    
    await asyncio.sleep(5)
    
    from keyboards import get_cancel_kb
    await query.message.answer(
        "📝 Напиши ниже свой вопрос или тему, которую хочешь разобрать:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(OnlineLessonStates.waiting_for_topic)


@router.message(OnlineLessonStates.waiting_for_topic)
async def receive_lesson_topic(message: Message, state: FSMContext, bot: Bot):
    """Получение темы урока."""
    user = message.from_user
    if not user:
        return

    if not message.text:
        await message.answer("Пожалуйста, напишите вашу тему или вопрос текстом.")
        return

    await state.update_data(topic=message.text, user_id=user.id)
    save_checkpoint(user.id, "ONLINE_LESSON_TOPIC", f"Тема: {message.text[:50]}")

    # Вычисляем дату через 2 дня
    from datetime import datetime, timedelta
    example_date = datetime.now() + timedelta(days=3)
    month_names = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
        7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    example_date_str = f"{example_date.day} {month_names[example_date.month]}"

    from keyboards import get_cancel_kb
    await message.answer(
        "Отлично! Теперь укажи желаемую дату и время урока.\n\n"
        "⚠️ Обратите внимание: запись возможна не позже, чем за <b>1 день</b>.\n\n"
        f"Например: <code>{example_date_str} 15:00</code> или <code>послезавтра в 18:30</code>",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(OnlineLessonStates.waiting_for_datetime)


@router.message(OnlineLessonStates.waiting_for_datetime)
async def receive_lesson_datetime(message: Message, state: FSMContext, bot: Bot):
    """Получение даты и времени урока."""
    user = message.from_user
    if not user:
        return

    if not message.text:
        await message.answer("⚠️ Пожалуйста, укажите дату и время.")
        return

    data = await state.get_data()
    topic = data.get("topic", "Не указана")
    datetime_str = message.text

    save_checkpoint(
        user.id,
        "ONLINE_LESSON_REQUEST",
        f"Тема: {topic[:30]}, Дата/время: {datetime_str[:30]}"
    )

    # Отправляем запрос админу
    name = user.first_name or "Без имени"
    uname = f"@{user.username}" if user.username else "нет username"
    
    admin_message = (
        f"📅 <b>Запрос на онлайн-урок</b>\n\n"
        f"👤 {name} ({uname})\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"<b>Тема:</b> {topic}\n"
        f"<b>Дата/время:</b> {datetime_str}\n\n"
        f"Для ответа используйте:\n"
        f"<code>/reply {user.id} текст</code>"
    )

    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, admin_message, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Не удалось отправить запрос админу {admin_id}: {e}")

    from keyboards import get_online_lesson_payment_kb

    await message.answer(
        "✅ Ваш запрос отправлен!\n\n"
        "Наш куратор свяжется с вами в ближайшее время для подтверждения записи.\n\n"
        "Вы можете сразу оплатить урок или уточнить детали:",
        reply_markup=get_online_lesson_payment_kb(config.sbp_phone)
    )
    await state.clear()


@router.callback_query(F.data == "show_sbp_payment")
async def show_sbp_payment(query: CallbackQuery):
    """Показать номер телефона для оплаты по СБП (онлайн-урок)."""
    await query.answer()
    await query.message.answer(
        f"💳 <b>Оплата по СБП</b>\n\n"
        f"Для оплаты онлайн-урока переведите <b>1500 рублей</b> по номеру телефона:\n\n"
        f"📱 <code>{config.sbp_phone}</code> (Валерия Дмитривна Б.)\n\n"
        f"<i>Нажмите на номер, чтобы скопировать</i>\n\n"
        f"После оплаты напишите куратору для подтверждения: @helionstudio",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "show_gift_sbp_payment")
async def show_gift_sbp_payment(query: CallbackQuery, bot: Bot):
    """Показать информацию об оплате подарочного сертификата по СБП."""
    await query.answer()
    
    # Отправляем изображение курса
    course_image_path = os.path.join(config.base_dir, "media", "docs", "course_info.jpg")
    if os.path.exists(course_image_path):
        await bot.send_photo(
            chat_id=query.message.chat.id,
            photo=FSInputFile(course_image_path)
        )
        await asyncio.sleep(2)
    
    await query.message.answer(
        f"💳 <b>Оплата подарочного сертификата по СБП</b>\n\n"
        f"💎 <b>Полный курс по рисованию в аниме-стиле</b>\n"
        f"Стоимость: <b>6 990 рублей</b>\n\n"
        f"📚 <b>Что включено:</b>\n"
        f"• 12 видео-уроков + домашние задания\n"
        f"• Мини-уроки и шпаргалки\n"
        f"• Закрытый чат со 150+ художниками\n"
        f"• Проверка домашних заданий и работа над ошибками\n"
        f"• Памятный сертификат о прохождении курса\n"
        f"• Бонусные уроки\n"
        f"• Экзамен и вступление в команду художников\n\n"
        f"🎁 <b>Бонус:</b> курс Photoshop в подарок!\n\n"
        f"📱 СБП для оплаты: <code>{config.sbp_phone}</code> (Валерия Дмитриевна Б.)\n\n"
        f"<i>Нажмите на номер, чтобы скопировать</i>\n\n"
        f"После оплаты напишите куратору для подтверждения: @helionstudio",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cancel_gift_certificate")
async def cancel_gift_certificate(query: CallbackQuery, state: FSMContext):
    """Отмена оформления подарочного сертификата."""
    await state.clear()
    await query.message.edit_text("❌ Оформление сертификата отменено.")
    await query.answer()


@router.callback_query(F.data == "cancel_online_lesson")
async def cancel_online_lesson(query: CallbackQuery, state: FSMContext):
    """Отмена записи на онлайн-урок."""
    await state.clear()
    await query.message.edit_text("❌ Запись отменена.")
    await query.answer()


# ─── Оформить подарочный сертификат ─────────────────────────

@router.callback_query(F.data == "menu_gift_certificate")
async def menu_gift_certificate(query: CallbackQuery, state: FSMContext, bot: Bot):
    """Оформление подарочного сертификата."""
    user = query.from_user
    save_checkpoint(user.id, "MENU_GIFT_CERTIFICATE", "Нажал 'Оформить подарочный сертификат'")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Нажал 'Оформить подарочный сертификат'"
    )
    await query.answer()

    # Отправляем фото с описанием сертификата
    course_image_path = os.path.join(config.base_dir, "media", "docs", "course_info.jpg")
    if os.path.exists(course_image_path):
        await bot.send_photo(
            chat_id=query.message.chat.id,
            photo=FSInputFile(course_image_path),
            caption=(
                "<b>Подарочный сертификат на обучение</b>\n\n"
                "Это отличный способ порадовать близкого человека и помочь ему открыть в себе талант художника!\n\n"
                "💝 <b>Что входит:</b>\n"
                "• Доступ к полному видео-курсу\n"
                "• Обратная связь от художников\n"
                "• Проверка домашних заданий\n"
                "• Дополнительные материалы\n\n"
                "📝 Давайте оформим сертификат!"
            ),
            parse_mode="HTML"
        )
    else:
        await query.message.answer(
            "<b>Подарочный сертификат на обучение</b>\n\n"
            "Это отличный способ порадовать близкого человека и помочь ему открыть в себе талант художника!\n\n"
            "💝 <b>Что входит:</b>\n"
            "• Доступ к полному видео-курсу\n"
            "• Обратная связь от художников\n"
            "• Проверка домашних заданий\n"
            "• Дополнительные материалы\n\n"
            "📝 Давайте оформим сертификат!",
            parse_mode="HTML"
        )

    await asyncio.sleep(3)

    from keyboards import get_cancel_gift_kb
    await query.message.answer(
        "Введите <b>имя получателя</b> подарка:\n\n"
        "<i>(Так оно будет указано в сертификате)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_gift_kb()
    )
    await state.set_state(GiftCertificateStates.waiting_for_recipient_name)


@router.message(GiftCertificateStates.waiting_for_recipient_name)
async def receive_recipient_name(message: Message, state: FSMContext, bot: Bot):
    """Получение имени получателя сертификата."""
    user = message.from_user
    if not user:
        return

    if not message.text:
        await message.answer("⚠️ Пожалуйста, введите имя текстом.")
        return

    recipient_name = message.text
    save_checkpoint(
        user.id,
        "GIFT_CERTIFICATE_RECIPIENT",
        f"Имя получателя: {recipient_name[:50]}"
    )

    # Отправляем запрос админу
    name = user.first_name or "Без имени"
    uname = f"@{user.username}" if user.username else "нет username"
    
    admin_message = (
        f"🎁 <b>Запрос на подарочный сертификат</b>\n\n"
        f"👤 От: {name} ({uname})\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"<b>Имя получателя:</b> {recipient_name}\n\n"
        f"Для ответа используйте:\n"
        f"<code>/reply {user.id} текст</code>"
    )

    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, admin_message, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Не удалось отправить запрос админу {admin_id}: {e}")

    from keyboards import get_gift_certificate_payment_kb
    
    await message.answer(
        f"Отлично! Сертификат на имя <b>{recipient_name}</b> оформляется!\n\n"
        f"Наш куратор свяжется с вами для уточнения деталей и оформления.\n\n"
        f"💰 <b>Стоимость курса: 6 990 рублей</b>\n\n"
        f"Вы можете сразу оплатить сертификат или уточнить детали у куратора: @helionstudio\n\n"
        f"📱 СБП для оплаты: <code>{config.sbp_phone}</code> (Валерия Дмитриевна Б.)\n\n"
        f"После оплаты напишите куратору для подтверждения.",
        parse_mode="HTML",
    )
    
    await state.clear()


@router.callback_query(F.data == "cancel_gift_certificate")
async def cancel_gift_certificate(query: CallbackQuery, state: FSMContext):
    """Отмена оформления подарочного сертификата."""
    await state.clear()
    await query.message.edit_text("❌ Оформление сертификата отменено.")
    await query.answer()


# ─── Получить туториал и шпаргалку ──────────────────────────

@router.callback_query(F.data == "menu_tutorial")
async def menu_tutorial(query: CallbackQuery, bot: Bot):
    """Отправка PDF-шпаргалки."""
    user = query.from_user
    save_checkpoint(user.id, "MENU_TUTORIAL", "Нажал «Получить туториал и шпаргалку»")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Нажал «Получить туториал и шпаргалку»"
    )
    await query.answer()

    name = user.first_name or "Приятель"
    
    # Проверяем наличие изображения-шпаргалки
    image_path = os.path.join(config.base_dir, "media", "docs", "tutorial_preview.jpg")
    if os.path.exists(image_path):
        await bot.send_photo(
            chat_id=query.message.chat.id,
            photo=FSInputFile(image_path)
        )
        await asyncio.sleep(5)
    
    # Отправляем текст
    await query.message.answer(f"{name}, получи шпаргалку по рисованию глаз 😍")
    await asyncio.sleep(5)
    
    await query.message.answer(
        "А в этой шпаргалке собраны интересные решения для аниме-художника!"
    )
    await asyncio.sleep(5)
    
    # Отправляем PDF
    pdf_path = os.path.join(config.base_dir, "media", "docs", "Советы и лайфхаки по рисованию.pdf")
    if os.path.exists(pdf_path):
        await bot.send_document(
            chat_id=query.message.chat.id,
            document=FSInputFile(pdf_path)
        )
    else:
        await query.message.answer(
            "😔 К сожалению, файл временно недоступен. "
            "Попробуй позже или обратись к куратору: @helionstudio"
        )
