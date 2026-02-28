"""
Profile and weight management handlers.
"""

import logging
import httpx
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ...config import settings
from ..keyboards.inline import create_profile_menu, create_weight_menu

logger = logging.getLogger(__name__)

router = Router()

# Initialize HTTP client
http_client = httpx.AsyncClient(timeout=30.0)


class WeightState(StatesGroup):
    """States for weight input."""
    waiting_for_weight = State()


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """
    Handle /profile command - show user profile and settings.
    """
    user = message.from_user
    logger.info(f"User {user.id} requested profile")

    try:
        # Get user profile from Agent API
        url = f"{settings.AGENT_API_URL}/v1/users/{user.id}/profile"
        response = await http_client.get(url)
        response.raise_for_status()

        profile = response.json()

        # Format profile text
        profile_text = "👤 **Ваш профиль**\n\n"

        # Personal info
        if profile.get("first_name"):
            profile_text += f"**Имя:** {profile['first_name']}"
            if profile.get("last_name"):
                profile_text += f" {profile['last_name']}"
            profile_text += "\n"

        # Physical parameters
        profile_text += "\n📊 **Физические параметры:**\n"

        if profile.get("age"):
            profile_text += f"• Возраст: {profile['age']} лет\n"

        if profile.get("gender"):
            gender_map = {"male": "Мужской", "female": "Женский", "other": "Другой"}
            profile_text += f"• Пол: {gender_map.get(profile['gender'], profile['gender'])}\n"

        if profile.get("height_cm"):
            profile_text += f"• Рост: {profile['height_cm']:.1f} см\n"

        if profile.get("weight_kg"):
            profile_text += f"• Вес: {profile['weight_kg']:.1f} кг\n"
        else:
            profile_text += "• Вес: не указан\n"

        if profile.get("activity_level"):
            activity_map = {
                "sedentary": "Сидячий",
                "lightly_active": "Легкая активность",
                "moderately_active": "Умеренная активность",
                "very_active": "Высокая активность",
                "extremely_active": "Очень высокая активность"
            }
            profile_text += f"• Активность: {activity_map.get(profile['activity_level'], profile['activity_level'])}\n"

        # Goals
        profile_text += "\n🎯 **Цели:**\n"

        if profile.get("goal"):
            goal_map = {
                "weight_loss": "Похудение",
                "muscle_gain": "Набор массы",
                "maintenance": "Поддержание веса",
                "health": "Здоровье"
            }
            profile_text += f"• Цель: {goal_map.get(profile['goal'], profile['goal'])}\n"

        if profile.get("target_calories"):
            profile_text += f"• Калории: {profile['target_calories']} ккал/день\n"

        if profile.get("target_protein"):
            profile_text += f"• Белки: {profile['target_protein']}г/день\n"

        if profile.get("target_carbs"):
            profile_text += f"• Углеводы: {profile['target_carbs']}г/день\n"

        if profile.get("target_fat"):
            profile_text += f"• Жиры: {profile['target_fat']}г/день\n"

        # Add instructions
        profile_text += "\n💡 Используйте:\n"
        profile_text += "• /settings - изменить настройки\n"
        profile_text += "• /weight - обновить вес\n"
        profile_text += "• /weight\\_history - история веса"

        await message.answer(profile_text, parse_mode="Markdown")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await message.answer("❌ Профиль не найден. Используйте /start для регистрации.")
        else:
            logger.error(f"HTTP error getting profile: {e}")
            await message.answer("❌ Ошибка получения профиля. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Error getting profile: {e}", exc_info=True)
        await message.answer("❌ Ошибка получения профиля. Попробуйте позже.")


@router.message(Command("weight"))
async def cmd_weight(message: Message, state: FSMContext):
    """
    Handle /weight command - add new weight entry.
    """
    await message.answer(
        "⚖️ Укажите ваш текущий вес в килограммах.\n\n"
        "Например: 75.5 или 80",
        parse_mode="Markdown"
    )
    await state.set_state(WeightState.waiting_for_weight)


@router.message(WeightState.waiting_for_weight)
async def process_weight_input(message: Message, state: FSMContext):
    """
    Process weight input from user.
    """
    user = message.from_user

    try:
        # Parse weight
        weight_text = message.text.strip().replace(",", ".")
        weight_kg = float(weight_text)

        if weight_kg <= 0 or weight_kg > 500:
            await message.answer("❌ Пожалуйста, укажите реальный вес (от 1 до 500 кг).")
            return

        # Send to Agent API
        url = f"{settings.AGENT_API_URL}/v1/users/{user.id}/weight"
        response = await http_client.post(
            url,
            json={"weight_kg": weight_kg}
        )
        response.raise_for_status()

        data = response.json()

        await message.answer(
            f"✅ Вес обновлен: **{weight_kg:.1f} кг**\n\n"
            "Используйте /weight\\_history чтобы посмотреть историю изменений.",
            parse_mode="Markdown"
        )

        await state.clear()

    except ValueError:
        await message.answer("❌ Неверный формат. Укажите число, например: 75.5")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error adding weight: {e}")
        await message.answer("❌ Ошибка сохранения веса. Попробуйте позже.")
        await state.clear()
    except Exception as e:
        logger.error(f"Error processing weight: {e}", exc_info=True)
        await message.answer("❌ Ошибка обработки веса. Попробуйте позже.")
        await state.clear()


@router.message(Command("weight_history"))
async def cmd_weight_history(message: Message):
    """
    Handle /weight_history command - show weight change history.
    """
    user = message.from_user
    logger.info(f"User {user.id} requested weight history")

    try:
        # Get weight history from Agent API
        url = f"{settings.AGENT_API_URL}/v1/users/{user.id}/weight/history"
        response = await http_client.get(url, params={"limit": 10})
        response.raise_for_status()

        data = response.json()
        entries = data.get("entries", [])
        weight_change = data.get("weight_change")

        if not entries:
            await message.answer(
                "📊 История веса пуста.\n\n"
                "Используйте /weight чтобы добавить первую запись."
            )
            return

        # Format history text
        history_text = "📊 **История веса** (последние 10 записей)\n\n"

        for entry in entries:
            weight = entry["weight_kg"]
            date = entry["measured_at"][:10]  # YYYY-MM-DD
            time = entry["measured_at"][11:16]  # HH:MM

            history_text += f"• {date} {time}: **{weight:.1f} кг**"

            if entry.get("notes"):
                history_text += f" _{entry['notes']}_"

            history_text += "\n"

        # Add weight change summary
        if weight_change is not None:
            history_text += "\n"
            if weight_change > 0:
                history_text += f"📈 Изменение: +{abs(weight_change):.1f} кг (за период)\n"
            elif weight_change < 0:
                history_text += f"📉 Изменение: -{abs(weight_change):.1f} кг (за период)\n"
            else:
                history_text += "➡️ Вес не изменился\n"

        history_text += "\n💡 Используйте /weight чтобы добавить новую запись"

        await message.answer(history_text, parse_mode="Markdown")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await message.answer("❌ Профиль не найден. Используйте /start для регистрации.")
        else:
            logger.error(f"HTTP error getting weight history: {e}")
            await message.answer("❌ Ошибка получения истории. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Error getting weight history: {e}", exc_info=True)
        await message.answer("❌ Ошибка получения истории. Попробуйте позже.")
