"""
Report handlers for /today and /week commands.
"""

import logging
import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date, timedelta, datetime

from ...config import settings

logger = logging.getLogger(__name__)

router = Router()

# Initialize HTTP client for report endpoints
http_client = httpx.AsyncClient(timeout=30.0)


@router.message(Command("today"))
async def cmd_today(message: Message):
    """
    Handle /today command - show daily report.
    """
    user = message.from_user
    logger.info(f"User {user.id} requested daily report")

    try:
        # Call Agent API report endpoint
        url = f"{settings.AGENT_API_URL}/v1/reports/today/{user.id}"
        response = await http_client.get(url)
        response.raise_for_status()

        data = response.json()
        report_text = data.get("formatted_text", "Нет данных")

        await message.answer(report_text, parse_mode="Markdown")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await message.answer("❌ Пользователь не найден. Используйте /start для регистрации.")
        else:
            logger.error(f"HTTP error getting daily report: {e}")
            await message.answer("❌ Ошибка получения отчёта. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Error getting daily report: {e}", exc_info=True)
        await message.answer("❌ Ошибка получения отчёта. Попробуйте позже.")


@router.message(Command("week"))
async def cmd_week(message: Message):
    """
    Handle /week command - show weekly report.
    """
    user = message.from_user
    logger.info(f"User {user.id} requested weekly report")

    try:
        # Call Agent API report endpoint
        url = f"{settings.AGENT_API_URL}/v1/reports/week/{user.id}"
        response = await http_client.get(url)
        response.raise_for_status()

        data = response.json()
        report_text = data.get("formatted_text", "Нет данных")

        await message.answer(report_text, parse_mode="Markdown")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await message.answer("❌ Пользователь не найден. Используйте /start для регистрации.")
        else:
            logger.error(f"HTTP error getting weekly report: {e}")
            await message.answer("❌ Ошибка получения отчёта. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Error getting weekly report: {e}", exc_info=True)
        await message.answer("❌ Ошибка получения отчёта. Попробуйте позже.")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handle /help command.
    """
    help_text = """🤖 **Помощь по использованию бота**

━━━━━━━━━━━━━━━━━━━━━━
📱 **ОСНОВНЫЕ КОМАНДЫ**
━━━━━━━━━━━━━━━━━━━━━━

/start - Начать работу с ботом
/profile - Показать ваш профиль
/settings - Настройка целей (калории, БЖУ)
/weight - Обновить текущий вес
/weight\\_history - История изменения веса
/delete - Удалить запись из дневника
/today - Отчёт за сегодня с прогрессом
/week - Недельный отчёт и статистика
/help - Эта подробная справка

━━━━━━━━━━━━━━━━━━━━━━
🍽️ **СПОСОБЫ ДОБАВЛЕНИЯ ЕДЫ**
━━━━━━━━━━━━━━━━━━━━━━

**1️⃣ Простой текст (поиск в FatSecret):**
• "Съел 2 яйца и 150г гречки"
• "200г курицы вареной и салат"
• "Протеиновый батончик 60г"

Бот найдёт продукты в базе FatSecret и покажет точные нутриенты.

**2️⃣ Прямой ввод КБЖУ:**
• "150г салат БЖУ 50/50/50 калорий 600"
• "Каша КБЖУ 350/15/5/60"
• "Смузи калорий 250 БЖУ 10/5/40"

Укажите вес и нутриенты - бот сразу добавит в дневник.

**3️⃣ Данные с упаковки (на 100г):**
• "Творог БЖУ 18/9/1 на 100г" → бот спросит вес
• "200г курица, на 100г: калории 165, белки 31, жиры 3.6"

Бот автоматически пересчитает на ваш вес!

**4️⃣ Фото этикетки (скоро):**
Отправьте фото упаковки - бот распознает нутриенты через AI

━━━━━━━━━━━━━━━━━━━━━━
⚙️ **НАСТРОЙКА ЦЕЛЕЙ**
━━━━━━━━━━━━━━━━━━━━━━

Используйте /settings для установки:
• **Цель:** Похудение / Набор массы / Поддержание
• **Калории:** Дневная норма (например, 2000 ккал)
• **Белки:** Целевое количество (например, 150г)
• **Жиры:** Целевое количество (например, 70г)
• **Углеводы:** Целевое количество (например, 200г)

После настройки в отчётах будут:
✅ Прогресс-бары
⚠️ Индикаторы достижения целей
💡 Умные рекомендации

━━━━━━━━━━━━━━━━━━━━━━
📊 **ОТЧЁТЫ**
━━━━━━━━━━━━━━━━━━━━━━

**/today** - Покажет за сегодня:
• Калории и БЖУ с прогресс-барами
• Процент выполнения целей
• Количество записей
• Персональные советы

**/week** - Покажет за неделю:
• График калорий по дням
• Средние значения КБЖУ
• Статистику активности
• Общие рекомендации

━━━━━━━━━━━━━━━━━━━━━━
❓ **УТОЧНЕНИЯ**
━━━━━━━━━━━━━━━━━━━━━━

Бот может спрашивать:
• **Вес:** "Сколько грамм вы съели?"
• **Способ приготовления:** "Гречка сухая или варёная?"
• **Выбор продукта:** Если найдено несколько вариантов
• **Порция:** Если на упаковке указано "на 100г"

Просто ответьте на вопрос - бот запомнит контекст!

━━━━━━━━━━━━━━━━━━━━━━
✨ **ПОЛЕЗНЫЕ СОВЕТЫ**
━━━━━━━━━━━━━━━━━━━━━━

• Указывайте вес в граммах для точности
• Уточняйте способ приготовления (варёное/жареное)
• Используйте прямой ввод КБЖУ для домашних блюд
• Настройте цели для персональных рекомендаций
• Проверяйте отчёты каждый день для мотивации

━━━━━━━━━━━━━━━━━━━━━━
🔒 **НАДЁЖНОСТЬ ДАННЫХ**
━━━━━━━━━━━━━━━━━━━━━━

• Поиск продуктов через базу **FatSecret**
• Никаких выдуманных значений от AI
• Вы сами вводите КБЖУ для кастомных блюд
• Все расчёты проверяются математически

Есть вопросы? Просто напишите!"""

    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("delete"))
async def cmd_delete(message: Message):
    """
    Handle /delete command - show today's food entries for deletion.
    """
    user = message.from_user
    logger.info(f"User {user.id} requested deletion menu")

    try:
        # Get today's food log entries
        url = f"{settings.AGENT_API_URL}/v1/users/{user.id}/food-log"
        response = await http_client.get(url)
        response.raise_for_status()

        data = response.json()
        entries = data.get("entries", [])

        if not entries:
            await message.answer(
                "📝 Список пуст - сегодня вы ещё ничего не добавили.\n\n"
                "Используйте обычный текст для добавления еды."
            )
            return

        # Create message with entries
        text = "🗑️ **Удаление записей**\n\n"
        text += "Выберите запись для удаления:\n\n"

        # Create inline keyboard with delete buttons
        buttons = []
        for entry in entries:
            entry_id = entry["id"]
            food_name = entry["food_name"]
            calories = entry["calories"]
            consumed_time = datetime.fromisoformat(entry["consumed_at"]).strftime("%H:%M")

            # Format button text
            button_text = f"{consumed_time} • {food_name} ({calories:.0f} ккал)"

            # Truncate long names
            if len(button_text) > 60:
                button_text = button_text[:57] + "..."

            buttons.append([InlineKeyboardButton(
                text=f"❌ {button_text}",
                callback_data=f"delete_entry:{entry_id}"
            )])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await message.answer("❌ Профиль не найден. Используйте /start для регистрации.")
        else:
            logger.error(f"HTTP error getting food log: {e}")
            await message.answer("❌ Ошибка получения списка. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Error getting food log for deletion: {e}", exc_info=True)
        await message.answer("❌ Ошибка получения списка. Попробуйте позже.")
