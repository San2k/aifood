"""
FatSecret integration commands.

DISABLED: FatSecret OAuth 2.0 user authorization is not supported.
FatSecret API only supports client_credentials (server-to-server).
Food search functionality remains available through FatSecret API.

See FATSECRET_OAUTH_FINDINGS.md for details.
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from ...services.agent_client import AgentClient
from ...config import settings as app_settings

logger = logging.getLogger(__name__)

router = Router()

# Initialize agent client
agent_client = AgentClient(app_settings.AGENT_API_URL)

# ============================================================================
# FATSECRET OAUTH COMMANDS DISABLED
# Reason: FatSecret OAuth 2.0 does not support authorization code flow
# Only manual goal setup via /settings is available
# ============================================================================


@router.message(Command("connect_fatsecret"))
async def cmd_connect_fatsecret(message: Message):
    """
    DISABLED: FatSecret account connection not available.
    Informs user about manual goal setup alternative.
    """
    await message.answer(
        "ℹ️ **Подключение аккаунта FatSecret недоступно**\n\n"
        "К сожалению, FatSecret API не поддерживает подключение пользовательских аккаунтов "
        "через OAuth 2.0.\n\n"
        "**Что работает:**\n"
        "✅ Поиск продуктов в базе FatSecret\n"
        "✅ Получение пищевой ценности\n"
        "✅ Отслеживание питания в боте\n\n"
        "**Настройка целей:**\n"
        "Используйте команду /settings для ручной настройки ваших целей по КБЖУ.\n\n"
        "Все ваши данные сохраняются в боте, импорт из FatSecret не требуется.",
        parse_mode="Markdown"
    )


@router.message(Command("disconnect_fatsecret"))
async def cmd_disconnect_fatsecret(message: Message):
    """
    DISABLED: No FatSecret connections exist.
    """
    await message.answer(
        "ℹ️ **Нет подключенного аккаунта FatSecret**\n\n"
        "Подключение аккаунтов FatSecret не поддерживается.\n"
        "Используйте /settings для настройки целей.",
        parse_mode="Markdown"
    )


@router.message(Command("sync_fatsecret"))
async def cmd_sync_fatsecret(message: Message):
    """
    DISABLED: No FatSecret profile sync available.
    """
    await message.answer(
        "ℹ️ **Синхронизация с FatSecret недоступна**\n\n"
        "FatSecret API не предоставляет доступ к пользовательским профилям.\n\n"
        "Используйте /settings для настройки и обновления ваших целей по КБЖУ.",
        parse_mode="Markdown"
    )
