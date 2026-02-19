"""
Модуль конфигурации — загрузка настроек из .env
"""
import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    admin_ids: List[int]
    # Ссылки
    link_trial_lesson: str
    link_course_page: str
    # Оплата
    sbp_phone: str
    link_order_illustration: str
    link_vk_community: str
    link_test: str
    # Пути к медиа (относительно корня проекта)
    base_dir: str = ""


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise ValueError("BOT_TOKEN не задан в .env")

    admin_raw = os.getenv("ADMIN_ID", "")
    admin_ids = [int(x.strip()) for x in admin_raw.split(",") if x.strip().isdigit()]
    if not admin_ids:
        raise ValueError("ADMIN_ID не задан или некорректен в .env")

    base_dir = os.path.dirname(os.path.abspath(__file__))

    return Config(
        bot_token=token,
        admin_ids=admin_ids,
        sbp_phone=os.getenv("SBP_PHONE", ""),
        link_trial_lesson=os.getenv("LINK_TRIAL_LESSON", ""),
        link_course_page=os.getenv("LINK_COURSE_PAGE", ""),
        link_order_illustration=os.getenv("LINK_ORDER_ILLUSTRATION", ""),
        link_vk_community=os.getenv("LINK_VK_COMMUNITY", ""),
        link_test=os.getenv("LINK_TEST", ""),
        base_dir=base_dir,
    )
