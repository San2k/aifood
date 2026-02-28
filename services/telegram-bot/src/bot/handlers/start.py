"""
/start command handler.
"""

import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handle /start command.
    
    Registers new user and shows welcome message.
    """
    user = message.from_user
    logger.info(f"User {user.id} started bot")
    
    welcome_text = f"""👋 Привет, {user.first_name}!

Я помогу вам отслеживать питание с помощью ИИ.

📝 **Как пользоваться:**
• Просто напишите, что съели: "2 яйца и 150г гречки"
• Отправьте фото этикетки продукта
• Я задам уточняющие вопросы, если нужно
• Все данные из FatSecret API - без выдумок!

📊 **Команды:**
/today - отчёт за сегодня
/week - отчёт за неделю
/help - помощь

Начните прямо сейчас - напишите, что съели! 🍽️"""
    
    await message.answer(welcome_text)
