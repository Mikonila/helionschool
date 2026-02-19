"""
Воронка продаж — цепочка сообщений после «О школе Helion».
"""
import os
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from config import load_config
from database import save_checkpoint, update_funnel_stage
from keyboards import get_after_yes_kb, get_trial_lesson_kb
from handlers.start import notify_admin_checkpoint
import logging

router = Router()
config = load_config()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "funnel_yes_draw")
async def funnel_yes(query: CallbackQuery, bot: Bot):
    """Пользователь ответил 'Да' — хочет научиться рисовать."""
    user = query.from_user
    save_checkpoint(user.id, "FUNNEL_YES_DRAW", "Ответил «Да» на вопрос о рисовании")
    update_funnel_stage(user.id, "interested")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Ответил «Да» — хочет научиться рисовать"
    )
    await query.answer()

    await query.message.answer(
        "Круто! Тогда держи еще немного информации о том, что тебя ждет:",
        parse_mode="HTML"
    )

    await asyncio.sleep(2)

    await query.message.answer(
        "Помимо <b>уроков в записи</b>, которые научат рисовать "
        "персонажей и создавать анимации, у тебя всегда будет доступ "
        "к <b>нашему чату</b>, где ты сможешь задавать вопросы художникам, "
        "а они — помогать тебе работать над ошибками и с каждым "
        "днем рисовать все лучше ✨",
        parse_mode="HTML"
    )

    await asyncio.sleep(7)

    await query.message.answer(
        "Также наши художники проводят <b>онлайн-уроки "
        "по видео-связи</b>. Пробный урок на нашем сайте поможет "
        "понять, какой формат обучения тебе подходит больше всего!",
        reply_markup=get_after_yes_kb(config),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "funnel_no_draw")
async def funnel_no(query: CallbackQuery, bot: Bot):
    """Пользователь ответил 'Нет'."""
    user = query.from_user
    save_checkpoint(user.id, "FUNNEL_NO_DRAW", "Ответил «Нет» на вопрос о рисовании")
    update_funnel_stage(user.id, "not_interested")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Ответил «Нет» — не хочет рисовать"
    )
    await query.answer()

    await query.message.answer(
        "Жаль! Но если передумаешь — мы всегда рады 😊\n"
        "Ты всегда можешь вернуться в меню и посмотреть "
        "наши бесплатные материалы!"
    )


@router.callback_query(F.data == "funnel_more_online")
async def funnel_more_online(query: CallbackQuery, bot: Bot):
    """Узнать больше про онлайн-уроки."""
    user = query.from_user
    save_checkpoint(user.id, "FUNNEL_MORE_ONLINE", "Нажал «Узнать больше про онлайн-уроки»")
    update_funnel_stage(user.id, "exploring_online")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Нажал «Узнать больше про онлайн-уроки»"
    )
    await query.answer()

    # Примеры обратной связи - объединяем все фото
    feedback_dir = os.path.join(config.base_dir, "media", "feedback")
    
    # Собираем все файлы (и примеры до/после, и скриншот чата)
    all_feedback_files = []
    
    # Сначала примеры до/после
    feedback_examples = sorted([
        f for f in os.listdir(feedback_dir)
        if f.endswith("_15-20-21.jpg")
    ])
    all_feedback_files.extend(feedback_examples)
    
    # Затем скриншот чата
    chat_screenshot = "photo_2023-05-18_19-01-08.jpg"
    if os.path.exists(os.path.join(feedback_dir, chat_screenshot)):
        all_feedback_files.append(chat_screenshot)

    if all_feedback_files:
        await query.message.answer(
            "Примеры того, как преподаватели поправляют рисунок "
            "ученика и дают развёрнутый ответ. Ниже представлен пример "
            "до/после, а также советы от различных художников!\n"
            "Чем больше художников — тем более объективная оценка 💪"
        )

        media_group = []
        for fname in all_feedback_files:
            path = os.path.join(feedback_dir, fname)
            media_group.append(InputMediaPhoto(media=FSInputFile(path)))

        if media_group:
            await bot.send_media_group(
                chat_id=query.message.chat.id,
                media=media_group
            )
        
        await asyncio.sleep(10)
        
        # Предлагаем пройти тест
        from keyboards import get_test_kb
        await query.message.answer(
            "🎨 А ещё у нас есть интересный тест <b>\"Какой ты художник?\"</b>\n\n"
            "Пройди тест и получи <b>бонусный урок \"Построение лица в аниме-стиле\" всего за 1₽!</b> 🎁",
            reply_markup=get_test_kb(config),
            parse_mode="HTML"
        )
        
        await asyncio.sleep(7)
        
        # Предлагаем купить полный курс
        await query.message.answer(
            "💎 <b>Готов начать свой путь художника?</b>\n\n"
            "Полный курс по рисованию в аниме-стиле всего за <b>6 990 рублей</b>!\n\n"
            "📚 Что включено:\n"
            "• 12 видео-уроков + домашние задания\n"
            "• Мини-уроки и шпаргалки\n"
            "• Закрытый чат со 150+ художниками\n"
            "• Проверка домашних заданий и работа над ошибками\n"
            "• Памятный сертификат о прохождении курса\n"
            "• Бонусные уроки\n"
            "• Экзамен и вступление в команду художников\n\n"
            "🎁 <b>Бонус:</b> курс Photoshop в подарок!\n\n"
            "📅 Подписка на 30 дней\n"
            "💳 Старт обучения сразу после оплаты\n\n"
            "Свяжись с нашим куратором для оформления: @helionstudio",
            parse_mode="HTML"
        )

        await asyncio.sleep(5)
        
        await query.message.answer(
            "Хочешь попробовать? Тогда пройди наш пробный урок!",
            reply_markup=get_trial_lesson_kb(config)
        )
    else:
        await query.message.answer(
            "Наши художники разбирают рисунки учеников, обсуждают ошибки "
            "и подробно объясняют, что можно улучшить.\n"
            "Сейчас я не могу отправить фотографии из-за ошибки, но если тебе интересно — напиши куратору @helionstudio, и он скинет примеры обратной связи от преподавателей!"
        )


@router.callback_query(F.data == "funnel_online_lessons_info")
async def funnel_online_lessons_info(query: CallbackQuery, state, bot: Bot):
    """Информация об онлайн-занятиях из воронки."""
    from aiogram.fsm.context import FSMContext
    user = query.from_user
    save_checkpoint(user.id, "FUNNEL_ONLINE_LESSONS_INFO", "Нажал «Узнать об онлайн-занятиях»")
    await notify_admin_checkpoint(
        bot, user.id, user.username, user.first_name,
        "Нажал «Узнать об онлайн-занятиях»"
    )
    update_funnel_stage(user.id, "interested_online_lessons")
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
    
    # Запускаем FSM для записи
    from handlers.menu import OnlineLessonStates
    from keyboards import get_cancel_kb
    await query.message.answer(
        "📝 Напиши ниже свой вопрос или тему, которую хочешь разобрать:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(OnlineLessonStates.waiting_for_topic)
